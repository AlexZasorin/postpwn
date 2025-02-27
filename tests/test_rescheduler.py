import asyncio

from postpwn.api import FakeTodoistAPI
from postpwn.cli import RescheduleParams, postpwn

# Tests to make:

# When no token is provided, an error should be raised
# When no filter is provided, nothing should happen
# When no rules are passed in, all selected tasks should be rescheduled to the current day
# When rules are passed in, tasks should be rescheduled according to the rules using smart rescheduling, respecting max weight
# When rules are passed in and a max weight is set for each day, tasks are rescheduled according to the rules using smart rescheduling, respecting the daily max weight
# When dry run is enabled, no tasks should be updated
# When time zone is specified, tasks should be rescheduled properly according to that time zone
# Application should retry on failure
# Passing in a valid cron string triggers rescheduling on that cron schedule
# Passing invalid cron string raises an error

# How to treat items with overlapping labels?


def test_no_token() -> None:
    kwargs: RescheduleParams = {
        "token": None,
        "filter": "label:test",
        "rules": None,
        "dry_run": True,
        "time_zone": "UTC",
        "schedule": None,
    }

    fake_api = FakeTodoistAPI("VALID_TOKEN")
    loop = asyncio.new_event_loop()

    postpwn(fake_api, loop, **kwargs)
    loop.close()
