import random
from typing import Any, Optional

from faker import Faker
from todoist_api_python.models import Due, Duration, Task


def generate_id() -> str:
    fake = Faker()
    return fake.uuid4()


def generate_int(min_val: int = 1, max_val: int = 100) -> int:
    return random.randint(min_val, max_val)


def generate_text(words: int = 10, ext_word_list: list[str] | None = None) -> str:
    fake = Faker()

    generated_words = fake.words(words, ext_word_list=ext_word_list)

    return " ".join(generated_words)


def generate_datetime(before_now: bool = True, after_now: bool = False) -> str:
    fake = Faker()
    return (
        fake.date_time_this_month(before_now=before_now, after_now=after_now)
        .replace(hour=12, minute=0, second=0, microsecond=0)
        .strftime("%Y-%m-%dT%H:%M:%S")
    )


def generate_date(before_today: bool = True, after_today: bool = False) -> str:
    fake = Faker()
    return fake.date_this_month(
        before_today=before_today, after_today=after_today
    ).strftime("%Y-%m-%d")


def generate_timezone() -> str:
    fake = Faker()
    return fake.timezone()


def generate_url() -> str:
    fake = Faker()
    return fake.url()


def build_due(properties: Optional[dict[str, Any]] = None) -> Due:
    defaults = Due(
        date=generate_date(),
        is_recurring=False,
        datetime=generate_datetime(),
        string=generate_text(),
        timezone=generate_timezone(),
    )

    if properties is None:
        return defaults

    return Due(
        **{
            field: properties.get(field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )


def build_duration(properties: Optional[dict[str, Any]] = None) -> Duration:
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
            field: properties.get(field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )


def build_task(properties: Optional[dict[str, Any]] = None) -> Task:
    defaults = Task(
        assignee_id=generate_id(),
        assigner_id=generate_id(),
        comment_count=generate_int(),
        is_completed=False,
        content=generate_text(),
        created_at=generate_datetime(),
        creator_id=generate_id(),
        description=generate_text(),
        due=build_due(),
        id=generate_id(),
        labels=[generate_text(words=1) for _ in range(3)],
        order=generate_int(),
        parent_id=generate_id(),
        priority=1,
        project_id=generate_id(),
        section_id=generate_id(),
        url=generate_url(),
        duration=build_duration(),
    )

    if properties is None:
        return defaults

    return Task(
        **{
            field: properties.get(field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )
