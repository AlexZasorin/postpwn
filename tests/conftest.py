import asyncio
from asyncio import AbstractEventLoop
from typing import Generator

import pytest

from postpwn.cli import RescheduleParams


@pytest.fixture
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def reschedule_params() -> RescheduleParams:
    return {
        "token": "VALID_TOKEN",
        "filter": "label:test",
        "rules": None,
        "dry_run": False,
        "time_zone": "UTC",
        "schedule": None,
    }
