import asyncio
import logging
import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Coroutine, Unpack
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from tenacity import (
    WrappedFn,
    after_log,
    before_log,
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
)
from todoist_api_python.models import Due, Task

from postpwn.api import TodoistAPIProtocol, UpdateTaskInput
from postpwn.types import Rule, WeightConfig
from postpwn.weighted_task import WeightedTask

_ = load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def weighted_adapter(task: Task, rules: list[Rule] | None) -> WeightedTask | None:
    if rules is None:
        return WeightedTask(task, 0)

    filter_map: dict[str, int] = {
        rule.filter[1:]: rule.weight for rule in rules if rule.weight is not None
    }

    if not task.labels:
        logger.info("Task has no labels, ignoring...")
        return None

    label = next((label for label in task.labels if label in filter_map), None)
    if not label:
        logger.info("Task has no matching labels, ignoring...")
        return None

    weight = filter_map[label]

    return WeightedTask(task, weight)


def fill_my_sack(
    max_weight: int,
    tasks: list[WeightedTask],
) -> list[WeightedTask]:
    values = [0 for _ in range(max_weight + 1)]
    selected: list[list[WeightedTask]] = [[] for _ in range(max_weight + 1)]

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


def get_update_params(new_date: date, due: Due) -> UpdateTaskInput:
    update_params: UpdateTaskInput = {}

    if isinstance(due.date, datetime):  # type:ignore[call-arg]
        time = datetime.strptime(str(due.date), "%Y-%m-%d %H:%M:%S").time()  # type:ignore[call-arg]
        new_datetime = datetime.strptime(f"{new_date} {time}", "%Y-%m-%d %H:%M:%S")
        update_params["due_datetime"] = new_datetime
    else:
        new_datetime = datetime.strptime(str(new_date), "%Y-%m-%d")
        update_params["due_date"] = new_datetime.date()

    if due.string:
        update_params["due_string"] = due.string

    return update_params


def get_weekday_weight(weight_config: WeightConfig | int, date: date) -> int:
    if isinstance(weight_config, int):
        return weight_config

    weekday_mapping = [
        weight_config.monday,
        weight_config.tuesday,
        weight_config.wednesday,
        weight_config.thursday,
        weight_config.friday,
        weight_config.saturday,
        weight_config.sunday,
    ]

    return weekday_mapping[date.weekday()]


async def filter_tasks(api: TodoistAPIProtocol, query: str) -> list[Task]:
    tasks: list[Task] = []

    task_generator = await api.filter_tasks(query=query)
    async for task_list in task_generator:
        tasks.extend(task_list)

    return tasks


async def update_task(
    api: TodoistAPIProtocol, task_id: str, **update_params: Unpack[UpdateTaskInput]
):
    return await api.update_task(task_id, **update_params)


def build_retry(func: WrappedFn) -> WrappedFn:
    return retry(
        reraise=True,
        wait=wait_exponential_jitter(max=120),
        stop=stop_after_attempt(int(os.getenv("RETRY_ATTEMPTS", "3"))),
        before=before_log(logger, logging.INFO),
        after=after_log(logger, logging.INFO),
    )(func)


async def reschedule(
    api: TodoistAPIProtocol,
    filter: str,
    max_weight: WeightConfig | int,
    time_zone: str,
    curr_date: date | None,
    rules: list[Rule] | None = None,
    dry_run: bool = False,
) -> None:
    get_tasks_with_retry = build_retry(filter_tasks)

    tasks = await get_tasks_with_retry(api, filter)

    # Add weights based on rules
    weighted_tasks = [weighted_adapter(task, rules) for task in tasks]

    # Filter out None values
    weighted_tasks = [task for task in weighted_tasks if task is not None]

    weighted_tasks.sort(
        key=lambda task: datetime.fromisoformat(str(task.due.date))  # type:ignore[call-arg]
        if task.due
        else datetime.max.date(),
    )

    new_schedule: dict[date, list[WeightedTask]] = defaultdict(list)
    reschedule_date = curr_date or datetime.now(tz=ZoneInfo(time_zone)).date()
    while len(weighted_tasks) != 0:
        weight = get_weekday_weight(max_weight, reschedule_date)
        next_batch = fill_my_sack(weight, weighted_tasks)

        new_schedule[reschedule_date].extend(next_batch)
        weighted_tasks = [task for task in weighted_tasks if task not in next_batch]

        reschedule_date += timedelta(days=1)

    update_coroutines: list[Coroutine[Any, Any, Task]] = []
    for new_date, weighted_tasks in new_schedule.items():
        for task in weighted_tasks:
            if task.due and (
                (isinstance(task.due.date, date) and task.due.date != new_date)  # type:ignore[call-arg]
                or (
                    isinstance(task.due.date, datetime)  # type:ignore[call-arg]
                    and task.due.date.date() != new_date  # type:ignore[call-arg]
                )
            ):
                update_params = get_update_params(new_date, task.due)

                logger.info(
                    f"Rescheduling {task.content} from {task.due.date} to {update_params['due_date'] if 'due_date' in update_params else update_params['due_datetime']}"  # type:ignore[call-arg]
                )
                if not dry_run:
                    update_task_with_retry = build_retry(update_task)
                    update_coroutines.append(
                        update_task_with_retry(api, task.id, **update_params)
                    )

    # Wait for all update tasks to complete
    if update_coroutines:
        await asyncio.gather(*update_coroutines)
