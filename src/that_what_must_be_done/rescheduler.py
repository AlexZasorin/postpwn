from asyncio import Task as AsyncTask, create_task
from collections import defaultdict
from datetime import datetime, timedelta

from todoist_api_python.api_async import TodoistAPIAsync
from todoist_api_python.models import Due, Task

from that_what_must_be_done.types import Rule, UpdateTaskParams
from that_what_must_be_done.weighted_task import WeightedTask

# TODO: Allow a maximum_weight for each day

# TODO: Somehow consider nonrecurring p1 tasks in scheduling calculation?


# TODO: Add value property to WeightedTask and increase value for older tasks
# Perhaps, take the difference between the current date and the oldest task, and normalize that
# to a value between 0 and 1, then add that to the weight of the task. This way, older tasks
# are prioritized over newer tasks, but will not be prioritized over tasks with higher priority.
# TODO: Add a limit to the rules, so that only a certain number of tasks can be scheduled per day
def weighted_adapter(task: Task, rules: list[Rule] | None) -> WeightedTask | None:
    if rules is None:
        return WeightedTask(task, 0)

    filter_map = {
        rule["filter"][1:]: rule["weight"] for rule in rules if "weight" in rule
    }

    if not task.labels:
        print("Task has no labels, ignoring...")
        return

    label = next((label for label in task.labels if label in filter_map), None)
    if not label:
        print("Task has no matching labels, ignoring...")
        return

    weight = filter_map[label]

    return WeightedTask(task, weight)


# TODO: Handle scheduling tasks with a limit set
def fill_my_sack(
    max_weight: int,
    tasks: list[WeightedTask],
) -> list[WeightedTask]:
    values = [0 for _ in range(max_weight + 1)]
    selected: list[list[WeightedTask]] = [list() for _ in range(max_weight + 1)]

    for task in tasks:
        for curr_capacity in range(max_weight, 0, -1):
            if task.weight <= curr_capacity:
                take = values[curr_capacity - task.weight] + task.priority
                dont_take = values[curr_capacity]

                if take > dont_take:
                    values[curr_capacity] = take
                    selected[curr_capacity] = selected[
                        curr_capacity - task.weight
                    ].copy()
                    selected[curr_capacity].append(task)

    return selected[max_weight]


def get_update_params(date_str: str, due: Due) -> UpdateTaskParams:
    update_params: UpdateTaskParams = {}
    if due.datetime:
        time = datetime.strptime(due.datetime, "%Y-%m-%dT%H:%M:%S").time()
        new_datetime = datetime.strptime(f"{date_str} {time}", "%Y-%m-%d %H:%M:%S")

        update_params["due_datetime"] = new_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        update_params["due_date"] = date_str

    if due.string:
        update_params["due_string"] = due.string

    return update_params


async def reschedule(
    api: TodoistAPIAsync,
    filter: str,
    max_weight: int,
    rules: list[Rule] | None = None,
) -> None:
    try:
        tasks = await api.get_tasks(filter=filter)  # pyright: ignore[reportUnknownMemberType]
    except Exception as error:
        print(error)
        tasks: list[Task] = []

    # Add weights based on rules
    weighted_tasks = [weighted_adapter(task, rules) for task in tasks]

    # Filter out None values
    weighted_tasks = [task for task in weighted_tasks if task is not None]

    weighted_tasks.sort(
        key=lambda task: task.due.date if task.due else datetime.max.date(),
    )

    new_schedule: dict[str, list[WeightedTask]] = defaultdict(list)
    curr_date = datetime.now().date()
    while len(weighted_tasks) != 0:
        next_batch = fill_my_sack(max_weight, weighted_tasks)

        new_schedule[str(curr_date)].extend(next_batch)
        weighted_tasks = [task for task in weighted_tasks if task not in next_batch]

        curr_date += timedelta(days=1)

    # We need to keep track of (async)tasks so they don't get garbage collected? lol
    coroutines: set[AsyncTask[bool]] = set()
    for date_str, weighted_tasks in new_schedule.items():
        for task in weighted_tasks:
            if task.due and task.due.date != date_str:
                print(f"Rescheduling task from {task.due.date} to {date_str}")

                update_params = get_update_params(date_str, task.due)

                result = create_task(api.update_task(task.id, **update_params))  # pyright: ignore[reportUnknownMemberType]
                coroutines.add(result)

                print(task.content)

    # Wait to finish so that the program doesn't exit early
    for coroutine in coroutines:
        await coroutine
