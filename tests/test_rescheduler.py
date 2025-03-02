import asyncio
from typing import Generator

import pytest
from requests import HTTPError

from postpwn.api import FakeTodoistAPI
from postpwn.cli import RescheduleParams, postpwn
from postpwn.testing.set_env import set_env

# TODO: Tests to make:
# [X] When no token is provided, an error should be raised
# When no filter is provided, nothing should happen
# When no rules are passed in, all selected tasks should be rescheduled to the current day
# When rules are passed in, tasks should be rescheduled according to the rules using smart rescheduling, respecting max weight
# When rules are passed in and a max weight is set for each day, tasks are rescheduled according to the rules using smart rescheduling, respecting the daily max weight
# When dry run is enabled, no tasks should be updated
# When time zone is specified, tasks should be rescheduled properly according to that time zone
# Application should retry on failure
# Passing in a valid cron string triggers rescheduling on that cron schedule
# Passing invalid cron string raises an error

# TODO: How to treat items with overlapping labels?


@pytest.fixture
def fake_api() -> FakeTodoistAPI:
    return FakeTodoistAPI("")


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# pyright: reportUnusedFunction=false
class TestPostpwn:
    """function `postpwn`"""

    def test_no_token_provided(
        self, fake_api: FakeTodoistAPI, event_loop: asyncio.AbstractEventLoop
    ) -> None:
        """raises an error when no token is provided"""

        kwargs: RescheduleParams = {
            "token": None,
            "filter": "label:test",
            "rules": None,
            "dry_run": True,
            "time_zone": "UTC",
            "schedule": None,
        }
        with set_env({"RETRY_ATTEMPTS": "1"}):
            with pytest.raises(HTTPError):
                postpwn(fake_api, event_loop, **kwargs)
