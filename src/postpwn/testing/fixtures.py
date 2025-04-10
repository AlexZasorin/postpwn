import random
from typing import Any, Optional

from faker import Faker
from todoist_api_python.models import Due, Duration, Task


def id_fixture() -> str:
    fake = Faker()
    return fake.uuid4()


def int_fixture(min_val: int = 1, max_val: int = 100) -> int:
    return random.randint(min_val, max_val)


def text_fixture(words: int = 10, ext_word_list: list[str] | None = None) -> str:
    fake = Faker()

    generated_words = fake.words(words, ext_word_list=ext_word_list)

    return " ".join(generated_words)


def datetime_fixture(before_now: bool = True, after_now: bool = False) -> str:
    fake = Faker()
    return str(fake.date_time_this_month(before_now=before_now, after_now=after_now))


def date_fixture() -> str:
    fake = Faker()
    return str(fake.date_this_month(before_today=False, after_today=True))


def timezone_fixture() -> str:
    fake = Faker()
    return fake.timezone()


def url_fixture() -> str:
    fake = Faker()
    return fake.url()


def due(properties: Optional[Due] = None) -> Due:
    defaults = Due(
        date=datetime_fixture(),
        is_recurring=False,
        datetime=datetime_fixture(before_now=False, after_now=True),
        string=text_fixture(),
        timezone=timezone_fixture(),
    )

    if properties is None:
        return defaults

    return Due(
        **{
            field: getattr(properties, field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )


def duration(properties: dict[str, Any] | None = None) -> Duration:
    defaults = Duration(
        amount=int_fixture(),
        # TODO: Create a separate fixture for generating random string literals
        # instead of using text fixture
        unit=text_fixture(words=1, ext_word_list=["minute", "day"]),
    )

    if properties is None:
        return defaults

    return Duration(
        **{
            field: getattr(properties, field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )


def task(properties: Optional[dict[str, Any]] = None) -> Task:
    defaults = Task(
        assignee_id=id_fixture(),
        assigner_id=id_fixture(),
        comment_count=int_fixture(),
        is_completed=False,
        content=text_fixture(),
        created_at=datetime_fixture(),
        creator_id=id_fixture(),
        description=text_fixture(),
        due=due(),
        id=id_fixture(),
        labels=[text_fixture(words=1) for _ in range(3)],
        order=int_fixture(),
        parent_id=id_fixture(),
        priority=1,
        project_id=id_fixture(),
        section_id=id_fixture(),
        url=url_fixture(),
        duration=duration(),
    )

    if properties is None:
        return defaults

    return Task(
        **{
            field: properties.get(field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )
