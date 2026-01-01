import asyncio
from asyncio import AbstractEventLoop
import logging
from typing import Generator

import pytest

from postpwn.cli import RescheduleParams


@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG, format="%(name)s [%(levelname)s]: %(message)s"
    )


@pytest.fixture
def loop() -> Generator[AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def params() -> RescheduleParams:
    return {
        "token": "VALID_TOKEN",
        "filter": "label:test",
        "rules": None,
        "dry_run": False,
        "time_zone": "UTC",
        "schedule": None,
    }
