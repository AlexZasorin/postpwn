import random
from datetime import date, datetime
from typing import Any, Optional

from dataclass_wizard import DatePattern, DateTimePattern
from faker import Faker
from todoist_api_python.models import Deadline, Due, Duration, Task


def generate_id() -> str:
    fake = Faker()
    return fake.uuid4()


def generate_int(min_val: int = 1, max_val: int = 100) -> int:
    return random.randint(min_val, max_val)


def generate_bool() -> bool:
    return random.choice([True, False])


def generate_text(words: int = 10, ext_word_list: list[str] | None = None) -> str:
    fake = Faker()

    generated_words = fake.words(words, ext_word_list=ext_word_list)

    return " ".join(generated_words)


def generate_datetime(before_now: bool = True, after_now: bool = False) -> datetime:
    fake = Faker()
    return fake.date_time_this_month(
        before_now=before_now, after_now=after_now
    ).replace(hour=0, minute=0, second=0, microsecond=0)


def generate_date(before_today: bool = True, after_today: bool = False) -> date:
    fake = Faker()
    fake.date
    return fake.date_this_month(before_today=before_today, after_today=after_today)


def generate_timezone() -> str:
    fake = Faker()
    return fake.timezone()


def generate_url() -> str:
    fake = Faker()
    return fake.url()


def build_due(
    properties: Optional[dict[str, Any]] = None, is_datetime: bool = False
) -> Due:
    defaults = Due(
        date=(  # pyright: ignore[reportArgumentType]
            DateTimePattern.fromisoformat(
                generate_datetime().strftime("%Y-%m-%dT%H:%M:%S")
            )
            if is_datetime
            else DatePattern.fromisoformat(generate_date().strftime("%Y-%m-%d"))
        ),
        is_recurring=False,
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
        # TODO: Create a separate fixture for generating random string
        # literals instead of using text fixture
        unit=random.choice(["minute", "day"]),
    )

    if properties is None:
        return defaults

    return Duration(
        **{
            field: properties.get(field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )


def build_deadline(properties: Optional[dict[str, Any]] = None) -> Deadline:
    defaults = Deadline(
        date=random.choice(  # pyright: ignore[reportArgumentType]
            [
                DatePattern.fromisoformat(generate_date().strftime("%Y-%m-%d")),
                DateTimePattern.fromisoformat(
                    generate_datetime().strftime("%Y-%m-%dT%H:%M:%S")
                ),
            ]
        ),
        lang="en",
    )

    if properties is None:
        return defaults

    return Deadline(
        **{
            field: properties.get(field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )


def build_task(
    properties: Optional[dict[str, Any]] = None, is_datetime: bool = False
) -> Task:
    defaults = Task(
        id=generate_id(),
        content=generate_text(),
        description=generate_text(),
        project_id=generate_id(),
        section_id=generate_id(),
        parent_id=generate_id(),
        labels=[generate_text(words=1) for _ in range(3)],
        priority=1,
        due=build_due(is_datetime=is_datetime),
        deadline=build_deadline(),
        duration=build_duration(),
        is_collapsed=generate_bool(),
        order=generate_int(),
        assignee_id=generate_id(),
        assigner_id=generate_id(),
        completed_at=None,
        creator_id=generate_id(),
        created_at=generate_datetime(),  # pyright: ignore[reportArgumentType]
        updated_at=generate_datetime(),  # pyright: ignore[reportArgumentType]
    )

    if properties is None:
        return defaults

    return Task(
        **{
            field: properties.get(field) or getattr(defaults, field)
            for field in defaults.__dict__
        }
    )
