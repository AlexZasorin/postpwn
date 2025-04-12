import asyncio
from asyncio import AbstractEventLoop
from typing import Generator

import pytest


@pytest.fixture
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
