import asyncio
from asyncio import AbstractEventLoop
import logging
from typing import Generator

import pytest

from postpwn.cli import RescheduleParams


@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)-10s %(name)-20s [%(levelname)-5s]: %(message)s",
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
        "filter": "view all",
        "rules": None,
        "dry_run": False,
        "time_zone": "UTC",
        "schedule": None,
        "consider_all_labeled": False,
    }
