import asyncio
import logging
from asyncio import AbstractEventLoop
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from helpers.data_generators import build_task
from helpers.fake_api import FakeTodoistAPI
from helpers.set_env import set_env
from requests import HTTPError

from postpwn.cli import RescheduleParams, postpwn
from postpwn.rescheduler import build_retry

# TODO: Tests to make:
# Hard - Passing in a valid cron string triggers rescheduling on that cron schedule and doesn't raise an error
# Hard - Test this as part of an E2E test? - When time zone is specified, tasks should be rescheduled properly according to that time zone

# TODO: How to treat items with overlapping labels? - Check for them, and then
# only reschedule according to the first rule that matches


logger = logging.getLogger(__name__)


@pytest.fixture
def fake_api():
    return FakeTodoistAPI("VALID_TOKEN")


def test_no_token_provided(loop: AbstractEventLoop, params: RescheduleParams) -> None:
    """when no token is provided, it raises an error"""

    params["token"] = None

    fake_api = FakeTodoistAPI("")

    curr_datetime = datetime(2022, 1, 5, 12, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        with pytest.raises(HTTPError, match="401 Client Error: Unauthorized for url"):
            postpwn(fake_api, loop, curr_datetime, **params)


def test_passing_invalid_cron_string_raises_error(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
) -> None:
    """when an invalid cron string is provided, it raises an error"""

    params["schedule"] = "invalid_cron_string"

    curr_datetime = datetime(2025, 1, 5, 12, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        with pytest.raises(ValueError, match="Invalid cron schedule."):
            postpwn(fake_api, loop, curr_datetime, **params)


def test_no_filter_provided(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
) -> None:
    """when no filter is provided, it does nothing"""

    params["filter"] = ""

    curr_datetime = datetime(2025, 1, 5, 12, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, loop, curr_datetime, **params)

    assert fake_api.update_task.call_count == 0


def test_no_rules_provided(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
) -> None:
    """when no rules are provided, it reschedules all tasks to the current day"""

    task = build_task()
    fake_api.setup_tasks([task])

    curr_date = datetime(2025, 1, 5, 0, 0, 0).date()

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, loop, curr_date, **params)

    assert fake_api.update_task.call_count == 1
    assert fake_api.update_task.call_args.kwargs["due_date"] == curr_date


def test_datetime_is_preserved(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
) -> None:
    """when a task has a datetime due date, the specific time is preserved"""

    task = build_task(is_datetime=True)
    fake_api.setup_tasks([task])

    curr_datetime = datetime(2025, 1, 5, 0, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, loop, curr_date=curr_datetime, **params)

    assert fake_api.update_task.call_count == 1
    assert fake_api.update_task.call_args.kwargs["due_datetime"] == curr_datetime


def test_weight_exceeds_single_max_weight(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
) -> None:
    """when a rule weight exceeds the singular max weight, it raises an error"""

    params["rules"] = "tests/fixtures/excessive_single_max_weight_rules.json"

    unlabeled_task = build_task()
    labeled_task = build_task({"labels": ["weight_one"]})

    fake_api.setup_tasks([unlabeled_task, labeled_task])

    curr_datetime = datetime(2025, 1, 5, 12, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        with pytest.raises(
            ValueError,
            match="Invalid rule config: @weight_two exceeds max weight 2",
        ):
            postpwn(fake_api, loop, curr_datetime, **params)


def test_weight_exceeds_daily_max_weight(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
) -> None:
    """when a rule exceeds one of the daily max weights, it raises an error"""

    params["rules"] = "tests/fixtures/excessive_daily_max_weight_rules.json"

    unlabeled_task = build_task()
    labeled_task = build_task({"labels": ["weight_one"]})

    fake_api.setup_tasks([unlabeled_task, labeled_task])

    curr_datetime = datetime(2025, 1, 5, 12, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        with pytest.raises(
            ValueError,
            match="Invalid rule config: @weight_two exceeds max weight 6",
        ):
            postpwn(fake_api, loop, curr_datetime, **params)


def test_no_matching_label(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
) -> None:
    """when tasks have no matching labels, they are not rescheduled"""

    params["rules"] = "tests/fixtures/single_max_weight_rules.json"

    unlabeled_task = build_task()
    labeled_task = build_task({"labels": ["weight_one"]})

    fake_api.setup_tasks([unlabeled_task, labeled_task])

    curr_datetime = datetime(2025, 1, 5, 12, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, loop, curr_datetime, **params)

    assert fake_api.update_task.call_count == 1
    assert fake_api.update_task.call_args.args[0] == labeled_task.id


def test_reschedule_with_rules(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
) -> None:
    """when rules are provided, it reschedules tasks using smart rescheduling, respecting max weight"""

    params["rules"] = "tests/fixtures/single_max_weight_rules.json"

    tasks = [
        *[build_task({"labels": ["weight_one"]}) for _ in range(2)],
        *[build_task({"labels": ["weight_two"]}, is_datetime=True) for _ in range(2)],
    ]

    fake_api.setup_tasks(tasks)

    curr_datetime = datetime(2025, 1, 5, 0, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, loop, curr_datetime, **params)

    assert fake_api.update_task.call_count == 4

    # Get distribution of scheduled tasks
    scheduled_dates = fake_api.task_distribution()

    # Current day (Jan 5)
    assert curr_datetime in scheduled_dates
    assert scheduled_dates[curr_datetime]["weight_one"] == 2
    assert scheduled_dates[curr_datetime]["weight_two"] == 0

    # Next day (Jan 6)
    second_day = curr_datetime + timedelta(days=1)
    assert second_day in scheduled_dates
    assert scheduled_dates[second_day]["weight_one"] == 0
    assert scheduled_dates[second_day]["weight_two"] == 1

    # Day after next (Jan 7)
    third_day = curr_datetime + timedelta(days=2)
    assert third_day in scheduled_dates
    assert scheduled_dates[third_day]["weight_one"] == 0
    assert scheduled_dates[third_day]["weight_two"] == 1


def test_reschedule_with_priority(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
) -> None:
    """when tasks have different priorities, it prioritizes the higher priority tasks first for rescheduling"""

    params["rules"] = "tests/fixtures/single_max_weight_rules.json"

    high_priority_task = build_task({"labels": ["weight_two"], "priority": 4})
    tasks = [
        *[build_task({"labels": ["weight_one"]}) for _ in range(2)],
        build_task({"labels": ["weight_two"]}, is_datetime=True),
        high_priority_task,
    ]

    fake_api.setup_tasks(tasks)

    curr_datetime = datetime(2025, 1, 5, 0, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, loop, curr_datetime, **params)

    assert fake_api.update_task.call_count == 4

    # Get distribution of scheduled tasks
    scheduled_dates = fake_api.task_distribution()

    # Current day (Jan 5)
    assert curr_datetime in scheduled_dates
    assert scheduled_dates[curr_datetime]["weight_one"] == 0
    assert scheduled_dates[curr_datetime]["weight_two"] == 1

    assert scheduled_dates[curr_datetime]["4"] == 1  # High priority task

    # Next day (Jan 6)
    second_day = curr_datetime + timedelta(days=1)
    assert second_day in scheduled_dates
    assert scheduled_dates[second_day]["weight_one"] == 2
    assert scheduled_dates[second_day]["weight_two"] == 0

    assert scheduled_dates[second_day]["1"] == 2

    # Day after next (Jan 7)
    third_day = curr_datetime + timedelta(days=2)
    assert third_day in scheduled_dates
    assert scheduled_dates[third_day]["weight_one"] == 0
    assert scheduled_dates[third_day]["weight_two"] == 1

    assert scheduled_dates[third_day]["1"] == 1


def test_reschedule_with_rules_and_daily_weight(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
):
    """when rules with a daily max weight are provided, it reschedules tasks using smart rescheduling, respecting the daily max weight"""

    params["rules"] = "tests/fixtures/daily_max_weight_rules.json"

    tasks = [
        *[build_task({"labels": ["weight_one"]}, is_datetime=True) for _ in range(3)],
        *[build_task({"labels": ["weight_two"]}) for _ in range(2)],
    ]

    fake_api.setup_tasks(tasks)

    curr_datetime = datetime(2025, 1, 5, 0, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, loop, curr_datetime, **params)

    assert fake_api.update_task.call_count == 5

    # Get distribution of scheduled tasks
    scheduled_dates = fake_api.task_distribution()

    # Current day (Jan 5)
    assert curr_datetime not in scheduled_dates
    assert scheduled_dates[curr_datetime]["weight_one"] == 0
    assert scheduled_dates[curr_datetime]["weight_two"] == 0

    # Next day (Jan 6)
    second_day = curr_datetime + timedelta(days=1)
    assert second_day in scheduled_dates
    assert scheduled_dates[second_day]["weight_one"] == 1
    assert scheduled_dates[second_day]["weight_two"] == 0

    # Day after next (Jan 7)
    third_day = curr_datetime + timedelta(days=2)
    assert third_day in scheduled_dates
    assert scheduled_dates[third_day]["weight_one"] == 2
    assert scheduled_dates[third_day]["weight_two"] == 0

    # Day...after that
    fourth_day = curr_datetime + timedelta(days=3)
    assert fourth_day in scheduled_dates
    assert scheduled_dates[fourth_day]["weight_one"] == 0
    assert scheduled_dates[fourth_day]["weight_two"] == 1

    # ...
    fifth_day = curr_datetime + timedelta(days=4)
    assert fifth_day in scheduled_dates
    assert scheduled_dates[fifth_day]["weight_one"] == 0
    assert scheduled_dates[fifth_day]["weight_two"] == 1


def test_dry_run_doesn_not_update_tasks(
    loop: AbstractEventLoop, params: RescheduleParams, fake_api: FakeTodoistAPI
) -> None:
    """when dry run is enabled, it does not reschedule tasks"""

    params["dry_run"] = True

    task = build_task()
    fake_api.setup_tasks([task])

    curr_datetime = datetime(2025, 1, 5, 12, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, loop, curr_datetime, **params)

    assert fake_api.update_task.call_count == 0


@pytest.mark.asyncio
async def test_retries_on_failure() -> None:
    """when function fails once then succeeds, it retries and returns result"""

    async def success_generator():
        yield [{"id": "123", "content": "Test"}]

    # Create mock that fails 2 times, then succeeds
    mock_func = AsyncMock(
        side_effect=[
            HTTPError("Fail 1"),
            success_generator(),
        ]
    )

    retrying_func = build_retry(mock_func)

    with set_env({"RETRY_ATTEMPTS": "2"}):
        result = await retrying_func(None, "test")
        tasks = []
        async for task_list in result:
            tasks.extend(task_list)  # pyright: ignore[reportUnknownMemberType]

    assert mock_func.call_count == 2
    assert len(tasks) == 1  # pyright: ignore[reportUnknownArgumentType]


@pytest.mark.asyncio
async def test_retries_exhaust_then_raises() -> None:
    """when function fails more than max retries, it raises the final error"""

    # Mock that always fails
    mock_func = AsyncMock(side_effect=HTTPError("Permanent failure"))
    retrying_func = build_retry(mock_func)

    with pytest.raises(HTTPError, match="Permanent failure"):
        with set_env({"RETRY_ATTEMPTS": "2"}):
            await retrying_func(None, "test")


@pytest.mark.asyncio
async def test_retry_respects_env_variable() -> None:
    """when RETRY_ATTEMPTS is set, it retries that many times"""

    # Mock that always fails
    mock_func = AsyncMock(side_effect=HTTPError("Always fails"))

    with set_env({"RETRY_ATTEMPTS": "3"}):
        # build_retry reads RETRY_ATTEMPTS at creation time
        retrying_func = build_retry(mock_func)
        try:
            await retrying_func(None, "test")
        except HTTPError:
            pass

    assert mock_func.call_count == 3
