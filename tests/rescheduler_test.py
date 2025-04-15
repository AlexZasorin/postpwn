import asyncio
from collections import defaultdict
import logging
import sys
from asyncio import AbstractEventLoop
from datetime import datetime, timedelta

import pytest
from helpers.data_generators import build_task
from helpers.set_env import set_env
from requests import HTTPError

from postpwn.api import FakeTodoistAPI
from postpwn.cli import RescheduleParams, postpwn

# TODO: Tests to make:
# Hard - Test this as part of an E2E test? - When time zone is specified, tasks should be rescheduled properly according to that time zone
# Medium/Hard - Application should retry on failure
# Hard - Passing in a valid cron string triggers rescheduling on that cron schedule
# Easy - Passing invalid cron string raises an error
# Easy - Tasks with labels that do not match the rules should not be rescheduled
# Easy - Rules with a weight > max weight should return an error
# Medium - With rules, tasks that have higher priority should be rescheduled first, according to knapsack algorithm

# TODO: How to treat items with overlapping labels?

logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

logger = logging.getLogger("postpwn")
logger.setLevel(logging.INFO)


def test_no_token_provided(event_loop: AbstractEventLoop) -> None:
    """when no token is provided, it raises an error"""

    kwargs: RescheduleParams = {
        "token": None,
        "filter": "label:test",
        "rules": None,
        "dry_run": True,
        "time_zone": "UTC",
        "schedule": None,
    }

    fake_api = FakeTodoistAPI("")

    curr_date = datetime(2022, 1, 1).date()

    with set_env({"RETRY_ATTEMPTS": "1"}):
        with pytest.raises(HTTPError):
            postpwn(fake_api, event_loop, curr_date, **kwargs)


def test_no_filter_provided(event_loop: AbstractEventLoop) -> None:
    """when no filter is provided, it does nothing"""

    kwargs: RescheduleParams = {
        "token": "VALID_TOKEN",
        "filter": "",
        "rules": None,
        "dry_run": False,
        "time_zone": "UTC",
        "schedule": None,
    }

    fake_api = FakeTodoistAPI("VALID_TOKEN")

    curr_date = datetime(2025, 1, 1).date()

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, event_loop, curr_date, **kwargs)

    assert fake_api.update_task.call_count == 0


def test_no_rules_provided(event_loop: asyncio.AbstractEventLoop) -> None:
    """when no rules are provided, it reschedules all tasks to the current day"""

    kwargs: RescheduleParams = {
        "token": "VALID_TOKEN",
        "filter": "label:test",
        "rules": None,
        "dry_run": False,
        "time_zone": "UTC",
        "schedule": None,
    }

    fake_api = FakeTodoistAPI("VALID_TOKEN")

    task = build_task()
    fake_api.setup_tasks([task])

    curr_date = datetime(2025, 1, 5).date()

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, event_loop, curr_date, **kwargs)

    assert fake_api.update_task.call_count == 1
    assert (
        fake_api.update_task.call_args.kwargs["due_datetime"] == "2025-01-05T12:00:00"
    )


def test_reschedule_with_rules(event_loop: AbstractEventLoop) -> None:
    """when rules are provided, it reschedules tasks using smart rescheduling, respecting max weight"""

    kwargs: RescheduleParams = {
        "token": "VALID_TOKEN",
        "filter": "label:test",
        "rules": "tests/fixtures/single_max_weight_rules.json",
        "dry_run": False,
        "time_zone": "UTC",
        "schedule": None,
    }

    fake_api = FakeTodoistAPI("VALID_TOKEN")

    tasks = [
        *[build_task({"labels": ["weight_one"]}) for _ in range(2)],
        *[build_task({"labels": ["weight_two"]}) for _ in range(2)],
    ]

    fake_api.setup_tasks(tasks)

    curr_datetime = datetime(2025, 1, 5, 12, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, event_loop, curr_datetime.date(), **kwargs)

    assert fake_api.update_task.call_count == 4

    # Group tasks by due_datetime
    calls = fake_api.update_task.call_args_list
    scheduled_dates: dict[str, list[str]] = defaultdict(list)

    for call in calls:
        task_id = call.args[0]
        due_datetime = call.kwargs["due_datetime"]

        matching_task = next(t for t in tasks if t.id == task_id)
        task_label = (
            "weight_one"
            if matching_task.labels and "weight_one" in matching_task.labels
            else "weight_two"
        )
        task_label = (
            next(label for label in matching_task.labels)
            if matching_task.labels
            else None
        )

        if task_label:
            scheduled_dates[due_datetime].append(task_label)

    format = "%Y-%m-%dT%H:%M:%S"

    # Current day (Jan 5)
    curr_date_str = curr_datetime.strftime(format)
    assert curr_date_str in scheduled_dates
    assert scheduled_dates[curr_date_str].count("weight_one") == 2
    assert scheduled_dates[curr_date_str].count("weight_two") == 0

    # Next day (Jan 6)
    second_day = (curr_datetime + timedelta(days=1)).strftime(format)
    assert second_day in scheduled_dates
    assert (
        scheduled_dates[second_day].count("weight_one") == 0
        and scheduled_dates[second_day].count("weight_two") == 1
    )

    # Day after next (Jan 7)
    third_day = (curr_datetime + timedelta(days=2)).strftime(format)
    assert third_day in scheduled_dates
    assert (
        scheduled_dates[third_day].count("weight_one") == 0
        and scheduled_dates[third_day].count("weight_two") == 1
    )


def test_reschedule_with_rules_and_daily_weight(event_loop: AbstractEventLoop):
    """when rules with a daily max weight are provided, it reschedules tasks using smart rescheduling, respecting the daily max weight"""

    kwargs: RescheduleParams = {
        "token": "VALID_TOKEN",
        "filter": "label:test",
        "rules": "tests/fixtures/daily_max_weight_rules.json",
        "dry_run": False,
        "time_zone": "UTC",
        "schedule": None,
    }

    fake_api = FakeTodoistAPI("VALID_TOKEN")

    tasks = [
        *[build_task({"labels": ["weight_one"]}) for _ in range(3)],
        *[build_task({"labels": ["weight_two"]}) for _ in range(2)],
    ]

    fake_api.setup_tasks(tasks)

    curr_datetime = datetime(2025, 1, 5, 12, 0, 0)

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, event_loop, curr_datetime.date(), **kwargs)

    assert fake_api.update_task.call_count == 5

    # Group tasks by due_datetime
    calls = fake_api.update_task.call_args_list
    scheduled_dates: dict[str, list[str]] = defaultdict(list)

    for call in calls:
        task_id = call.args[0]
        due_datetime = call.kwargs["due_datetime"]

        matching_task = next(t for t in tasks if t.id == task_id)
        task_label = (
            "weight_one"
            if matching_task.labels and "weight_one" in matching_task.labels
            else "weight_two"
        )
        task_label = (
            next(label for label in matching_task.labels)
            if matching_task.labels
            else None
        )

        if task_label:
            scheduled_dates[due_datetime].append(task_label)

    format = "%Y-%m-%dT%H:%M:%S"

    # Current day (Jan 5)
    curr_date_str = curr_datetime.strftime(format)
    assert curr_date_str not in scheduled_dates
    assert scheduled_dates[curr_date_str].count("weight_one") == 0
    assert scheduled_dates[curr_date_str].count("weight_two") == 0

    # Next day (Jan 6)
    second_day = (curr_datetime + timedelta(days=1)).strftime(format)
    assert second_day in scheduled_dates
    assert (
        scheduled_dates[second_day].count("weight_one") == 1
        and scheduled_dates[second_day].count("weight_two") == 0
    )

    # Day after next (Jan 7)
    third_day = (curr_datetime + timedelta(days=2)).strftime(format)
    assert third_day in scheduled_dates
    assert (
        scheduled_dates[third_day].count("weight_one") == 2
        and scheduled_dates[third_day].count("weight_two") == 0
    )

    # Day...after that
    fourth_day = (curr_datetime + timedelta(days=3)).strftime(format)
    assert fourth_day in scheduled_dates
    assert (
        scheduled_dates[fourth_day].count("weight_one") == 0
        and scheduled_dates[fourth_day].count("weight_two") == 1
    )

    # ...
    fifth_day = (curr_datetime + timedelta(days=4)).strftime(format)
    assert fifth_day in scheduled_dates
    assert (
        scheduled_dates[fifth_day].count("weight_one") == 0
        and scheduled_dates[fifth_day].count("weight_two") == 1
    )


def test_dry_run_doesn_not_update_tasks(event_loop: AbstractEventLoop) -> None:
    """when dry run is enabled, it does not reschedule tasks"""

    kwargs: RescheduleParams = {
        "token": "VALID_TOKEN",
        "filter": "label:test",
        "rules": None,
        "dry_run": True,
        "time_zone": "UTC",
        "schedule": None,
    }

    fake_api = FakeTodoistAPI("VALID_TOKEN")

    task = build_task()
    fake_api.setup_tasks([task])

    curr_date = datetime(2025, 1, 5).date()

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, event_loop, curr_date, **kwargs)

    assert fake_api.update_task.call_count == 0
