from functools import partial
import logging
import os
import sys

from asyncio import Task as AsyncTask, create_task
from collections import defaultdict
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
from todoist_api_python.models import Due, Task

from postpwn.api import TodoistAPIProtocol
from postpwn.types import Rule, UpdateTaskParams, WeightConfig
from postpwn.weighted_task import WeightedTask

from tenacity import (
    WrappedFn,
    after_log,
    before_log,
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
)

_ = load_dotenv()

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger(__name__)


def weighted_adapter(task: Task, rules: list[Rule] | None) -> WeightedTask | None:
    if rules is None:
        return WeightedTask(task, 0)

    filter_map = {
        rule["filter"][1:]: rule["weight"] for rule in rules if "weight" in rule
    }

    if not task.labels:
        logger.info("Task has no labels, ignoring...")
        return

    label = next((label for label in task.labels if label in filter_map), None)
    if not label:
        logger.info("Task has no matching labels, ignoring...")
        return

    weight = filter_map[label]

    return WeightedTask(task, weight)


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


def get_weekday_weight(weight_config: WeightConfig | int, date: date) -> int:
    if isinstance(weight_config, int):
        return weight_config

    match date.weekday():
        case 0:
            return weight_config.monday
        case 1:
            return weight_config.tuesday
        case 2:
            return weight_config.wednesday
        case 3:
            return weight_config.thursday
        case 4:
            return weight_config.friday
        case 5:
            return weight_config.saturday
        case 6:
            return weight_config.sunday
        case _:
            return 0


def build_retry(fn: WrappedFn) -> WrappedFn:
    return retry(
        reraise=True,
        wait=wait_exponential_jitter(max=120),
        stop=stop_after_attempt(int(os.getenv("RETRY_ATTEMPTS", 3))),
        before=before_log(logger, logging.DEBUG),
        after=after_log(logger, logging.DEBUG),
    )(fn)


async def reschedule(
    api: TodoistAPIProtocol,
    filter: str,
    max_weight: WeightConfig | int,
    curr_date: date,
    rules: list[Rule] | None = None,
    dry_run: bool = False,
) -> None:
    get_tasks = build_retry(partial(api.get_tasks, filter=filter))

    tasks = await get_tasks()

    # Add weights based on rules
    weighted_tasks = [weighted_adapter(task, rules) for task in tasks]

    # Filter out None values
    weighted_tasks = [task for task in weighted_tasks if task is not None]

    weighted_tasks.sort(
        key=lambda task: task.due.date if task.due else datetime.max.date(),
    )

    new_schedule: dict[str, list[WeightedTask]] = defaultdict(list)
    while len(weighted_tasks) != 0:
        weight = get_weekday_weight(max_weight, curr_date)
        next_batch = fill_my_sack(weight, weighted_tasks)

        new_schedule[str(curr_date)].extend(next_batch)
        weighted_tasks = [task for task in weighted_tasks if task not in next_batch]

        curr_date += timedelta(days=1)

    # We need to keep track of (async)tasks so they don't get garbage collected? lol
    coroutines: set[AsyncTask[bool]] = set()
    for date_str, weighted_tasks in new_schedule.items():
        for task in weighted_tasks:
            if task.due and task.due.date != date_str:
                logger.info(
                    f"Rescheduling {task.content} from {task.due.date} to {date_str}"
                )

                update_params = get_update_params(date_str, task.due)

                if not dry_run:
                    update_task = build_retry(
                        partial(api.update_task, task_id=task.id, kwargs=update_params)
                    )

                    result = create_task(update_task())
                    coroutines.add(result)

    # Wait to finish so that the program doesn't exit early
    for coroutine in coroutines:
        await coroutine
