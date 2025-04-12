import asyncio
from asyncio import AbstractEventLoop
from typing import Any, Generator, Optional

import pytest
from helpers.data_generators import (
    generate_datetime,
    generate_id,
    generate_int,
    generate_text,
    generate_timezone,
    generate_url,
)
from todoist_api_python.models import Due, Duration, Task


@pytest.fixture
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def due(properties: Optional[dict[str, Any]] = None) -> Due:
    defaults = Due(
        date=generate_datetime(),
        is_recurring=False,
        datetime=generate_datetime(before_now=False, after_now=True),
        string=generate_text(),
        timezone=generate_timezone(),
    )

    if properties is None:
        return defaults

    return Due(
        **{
            field: getattr(properties, field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )


@pytest.fixture
def duration(properties: Optional[dict[str, Any]] = None) -> Duration:
    defaults = Duration(
        amount=generate_int(),
        # TODO: Create a separate fixture for generating random string literals
        # instead of using text fixture
        unit=generate_text(words=1, ext_word_list=["minute", "day"]),
    )

    if properties is None:
        return defaults

    return Duration(
        **{
            field: getattr(properties, field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )


@pytest.fixture
def task(properties: Optional[dict[str, Any]] = None) -> Task:
    defaults = Task(
        assignee_id=generate_id(),
        assigner_id=generate_id(),
        comment_count=generate_int(),
        is_completed=False,
        content=generate_text(),
        created_at=generate_datetime(),
        creator_id=generate_id(),
        description=generate_text(),
        due=due(),
        id=generate_id(),
        labels=[generate_text(words=1) for _ in range(3)],
        order=generate_int(),
        parent_id=generate_id(),
        priority=1,
        project_id=generate_id(),
        section_id=generate_id(),
        url=generate_url(),
        duration=duration(),
    )

    if properties is None:
        return defaults

    return Task(
        **{
            field: getattr(properties, field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )
