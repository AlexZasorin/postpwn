import asyncio
import logging
from asyncio import AbstractEventLoop
from datetime import datetime

import pytest
from requests import HTTPError

from postpwn.api import FakeTodoistAPI
from postpwn.cli import RescheduleParams, postpwn

from helpers.set_env import set_env

# TODO: Tests to make:
# [X] When no token is provided, an error should be raised
# [X] When no filter is provided, nothing should happen
# [X] When no rules are passed in, all selected tasks should be rescheduled to the current day
# When rules are passed in, tasks should be rescheduled according to the rules using smart rescheduling, respecting max weight
# When rules are passed in and a max weight is set for each day, tasks are rescheduled according to the rules using smart rescheduling, respecting the daily max weight
# When dry run is enabled, no tasks should be updated
# When time zone is specified, tasks should be rescheduled properly according to that time zone
# Application should retry on failure
# Passing in a valid cron string triggers rescheduling on that cron schedule
# Passing invalid cron string raises an error

# TODO: How to treat items with overlapping labels?

logger = logging.getLogger("postpwn")
logger.setLevel(logging.DEBUG)


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

    curr_date = datetime(2025, 1, 1).date()

    with set_env({"RETRY_ATTEMPTS": "1"}):
        postpwn(fake_api, event_loop, curr_date, **kwargs)

    assert fake_api.update_task.call_count == 1
    assert (
        fake_api.update_task.call_args.kwargs["due_datetime"] == "2025-01-01T12:00:00"
    )
