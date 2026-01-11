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
from todoist_api_python.models import ApiDue, Due, Task

from postpwn.api import TodoistAPIProtocol, UpdateTaskInput
from postpwn.types import Rule, WeightConfig
from postpwn.weighted_task import WeightedTask

_ = load_dotenv()

logger = logging.getLogger(__name__)


def weighted_adapter(task: Task, rules: list[Rule] | None) -> WeightedTask | None:
    logger.debug(f"weighted_adapter: processing task '{task.content}' (id={task.id})")

    if rules is None:
        logger.debug("weighted_adapter: no rules provided, assigning weight=0")
        return WeightedTask(task, 0)

    filter_map: dict[str, int] = {
        rule.filter[1:]: rule.weight for rule in rules if rule.weight is not None
    }
    logger.debug(
        f"weighted_adapter: built filter_map with {len(filter_map)} entries: {filter_map}"
    )

    if not task.labels:
        logger.info("Task has no labels, ignoring...")
        return None

    logger.debug(f"weighted_adapter: task has labels: {task.labels}")
    label = next((label for label in task.labels if label in filter_map), None)
    if not label:
        logger.debug("Task has no matching labels, ignoring...")
        return None

    weight = filter_map[label]
    logger.debug(f"weighted_adapter: matched label '{label}', assigned weight={weight}")

    return WeightedTask(task, weight)


def fill_my_sack(
    max_weight: int,
    tasks: list[WeightedTask],
) -> list[WeightedTask]:
    logger.debug(
        f"fill_my_sack: starting knapsack with max_weight={max_weight}, {len(tasks)} tasks"
    )

    values = [0] * (max_weight + 1)
    selected: list[list[WeightedTask]] = [[] for _ in range(max_weight + 1)]

    for task in tasks:
        logger.debug(
            f"fill_my_sack: processing task '{task.content}' (weight={task.weight}, priority={task.priority})"
        )

        for curr_capacity in range(max_weight, 0, -1):
            if task.weight > curr_capacity:
                continue

            take = values[curr_capacity - task.weight] + task.priority
            dont_take = values[curr_capacity]

            if take <= dont_take:
                continue

            logger.debug(
                f"fill_my_sack: selected task '{task.content}' at capacity={curr_capacity} (take={take} > dont_take={dont_take})"
            )
            values[curr_capacity] = take
            selected[curr_capacity] = selected[curr_capacity - task.weight].copy()
            selected[curr_capacity].append(task)

    result = selected[max_weight]
    total_weight = sum(task.weight for task in result)
    total_value = sum(task.priority for task in result)
    logger.debug(
        f"fill_my_sack: completed, selected {len(result)} tasks (total_weight={total_weight}/{max_weight}, total_value={total_value})"
    )

    return result


def get_update_params(new_date: date, due: Due) -> UpdateTaskInput:
    logger.debug(
        f"get_update_params: creating params for new_date={new_date}, due.date={due.date} (type={type(due.date).__name__})"  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
    )

    update_params: UpdateTaskInput = {}

    if isinstance(due.date, datetime):  # pyright: ignore[reportUnknownMemberType]
        time = due.date.time()  # pyright: ignore[reportUnknownMemberType]
        update_params["due_datetime"] = datetime.combine(new_date, time)
        logger.debug(f"get_update_params: datetime task, preserving time={time}")
    else:
        update_params["due_date"] = new_date
        logger.debug("get_update_params: date-only task")

    if due.string:
        update_params["due_string"] = due.string
        logger.debug(f"get_update_params: preserving due_string='{due.string}'")

    return update_params


def calculate_weight_modifier(date: date, excluded_tasks: list[WeightedTask]):
    midnight_date = datetime.combine(date, datetime.min.time())
    logger.debug(
        f"calculate_weight_modifier: calculating for date={midnight_date} with {len(excluded_tasks)} excluded tasks"
    )

    matching_tasks = [
        task
        for task in excluded_tasks
        if task.due and task.due.date == midnight_date  # pyright: ignore[reportUnknownMemberType]
    ]

    for task in excluded_tasks:
        if task.due:
            logger.debug(f"excluded task {task.id} due date={task.due.date}")  # pyright: ignore[reportUnknownMemberType]

    logger.debug(f"{len(matching_tasks)} matching tasks found for date={midnight_date}")

    modifier = sum(task.weight for task in matching_tasks)

    if matching_tasks:
        logger.debug(
            f"calculate_weight_modifier: found {len(matching_tasks)} matching tasks: {[f'{t.content}(w={t.weight})' for t in matching_tasks]}"
        )

    logger.debug(f"weight modifier for {midnight_date}: {modifier}")

    return modifier


def get_weekday_weight(
    weight_config: WeightConfig | int,
    date: date,
    excluded_tasks: list[WeightedTask] | None,
) -> int:
    logger.debug(
        f"get_weekday_weight: calculating for date={date} ({date.strftime('%A')})"
    )

    if isinstance(weight_config, int):
        logger.debug(f"get_weekday_weight: using fixed weight={weight_config}")
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

    base_weight = weekday_mapping[date.weekday()]
    logger.debug(
        f"get_weekday_weight: base_weight={base_weight} for {date.strftime('%A')}"
    )

    weight_modifier = (
        calculate_weight_modifier(date, excluded_tasks) if excluded_tasks else 0
    )

    final_weight = max(base_weight - weight_modifier, 0)
    logger.debug(
        f"get_weekday_weight: final_weight={final_weight} (base={base_weight} - modifier={weight_modifier})"
    )

    return final_weight


async def filter_tasks(api: TodoistAPIProtocol, query: str) -> list[Task]:
    logger.debug(f"filter_tasks: fetching tasks with query='{query}'")
    tasks: list[Task] = []

    task_generator = await api.filter_tasks(query=query)
    async for task_list in task_generator:
        logger.debug(f"filter_tasks: received batch of {len(task_list)} tasks")
        tasks.extend(task_list)

    logger.debug(f"filter_tasks: completed, total tasks={len(tasks)}")
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


def is_already_scheduled(due_date: ApiDue, target_date: date) -> bool:  # pyright: ignore[reportUnknownParameterType]
    """Check if task is already scheduled on the target date."""
    if isinstance(due_date, datetime):
        return due_date.date() == target_date
    return due_date == target_date


async def reschedule(
    api: TodoistAPIProtocol,
    filter: str,
    max_weight: WeightConfig | int,
    time_zone: str,
    curr_date: date | None,
    consider_all_labeled: bool,
    rules: list[Rule] | None = None,
    dry_run: bool = False,
) -> None:
    logger.debug(
        f"reschedule: starting with filter='{filter}', time_zone='{time_zone}', dry_run={dry_run}, reschedule: max_weight={max_weight}, consider_all_labeled={consider_all_labeled}"
    )

    get_tasks_with_retry = build_retry(filter_tasks)

    tasks = await get_tasks_with_retry(api, filter)
    logger.debug(f"reschedule: fetched {len(tasks)} tasks from filter")

    # Add weights based on rules
    weighted_tasks_results = [weighted_adapter(task, rules) for task in tasks]

    # Filter out None values
    weighted_tasks: list[WeightedTask] = [
        task for task in weighted_tasks_results if task is not None
    ]
    logger.debug(
        f"reschedule: {len(weighted_tasks)} tasks have matching labels (filtered from {len(tasks)})"
    )

    weighted_tasks.sort(
        key=lambda task: datetime.fromisoformat(str(task.due.date))  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        if task.due
        else datetime.max
    )

    weighted_excluded_tasks: list[WeightedTask] = []
    if consider_all_labeled:
        logger.debug("reschedule: fetching excluded tasks (consider_all_labeled=True)")
        excluded_tasks = [
            task
            for task in await get_tasks_with_retry(api, f"!({filter})")
            if task not in tasks
        ]
        logger.debug(f"reschedule: found {len(excluded_tasks)} excluded tasks")

        weighted_excluded_tasks = [
            wt
            for task in excluded_tasks
            if (wt := weighted_adapter(task, rules)) is not None
        ]
        logger.debug(
            f"reschedule: {len(weighted_excluded_tasks)} excluded tasks have matching labels"
        )

        weighted_excluded_tasks.sort(
            key=lambda task: datetime.fromisoformat(str(task.due.date))  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            if task.due
            else datetime.max
        )

    new_schedule: dict[date, list[WeightedTask]] = defaultdict(list)
    reschedule_date = curr_date or datetime.now(tz=ZoneInfo(time_zone)).date()
    logger.debug(f"reschedule: starting date for rescheduling: {reschedule_date}")

    iteration = 0
    while weighted_tasks:
        iteration += 1
        logger.debug(
            f"reschedule: iteration {iteration} - {len(weighted_tasks)} tasks remaining, processing date {reschedule_date}"
        )

        weight = get_weekday_weight(
            max_weight, reschedule_date, weighted_excluded_tasks
        )
        next_batch = fill_my_sack(weight, weighted_tasks)

        logger.debug(
            f"reschedule: scheduled {len(next_batch)} tasks for {reschedule_date}"
        )

        new_schedule[reschedule_date].extend(next_batch)
        next_batch_ids = {task.id for task in next_batch}
        weighted_tasks = [
            task for task in weighted_tasks if task.id not in next_batch_ids
        ]

        reschedule_date += timedelta(days=1)

    update_coroutines: list[Coroutine[Any, Any, Task]] = []
    tasks_to_update = 0
    tasks_unchanged = 0

    for new_date, weighted_tasks in new_schedule.items():
        for task in weighted_tasks:
            if not task.due or is_already_scheduled(task.due.date, new_date):  # pyright: ignore[reportUnknownMemberType]
                logger.debug(
                    f"reschedule: task '{task.content}' already scheduled for {new_date}, skipping"
                )
                tasks_unchanged += 1
                continue

            update_params = get_update_params(new_date, task.due)

            logger.info(
                f"Rescheduling {task.content} from {task.due.date} to {update_params['due_date'] if 'due_date' in update_params else update_params['due_datetime']}"  # pyright: ignore[reportUnknownMemberType, reportTypedDictNotRequiredAccess]
            )
            tasks_to_update += 1

            if dry_run:
                continue

            update_task_with_retry = build_retry(update_task)
            update_coroutines.append(
                update_task_with_retry(api, task.id, **update_params)
            )

    logger.debug(
        f"reschedule: summary - {tasks_to_update} tasks to update, {tasks_unchanged} unchanged, dry_run={dry_run}"
    )

    # Wait for all update tasks to complete
    if update_coroutines:
        logger.debug(
            f"reschedule: executing {len(update_coroutines)} update operations"
        )
        await asyncio.gather(*update_coroutines)
