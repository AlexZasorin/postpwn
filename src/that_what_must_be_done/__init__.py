import asyncio
import os

from dotenv import load_dotenv
from todoist_api_python.api_async import TodoistAPIAsync

from that_what_must_be_done.rescheduler import reschedule
from that_what_must_be_done.types import Rule

config = load_dotenv()

max_weight = 10
rules: list[Rule] = [
    {"filter": "@< 15 min", "limit": 4, "weight": 2},
    {"filter": "@< 60 min", "weight": 4},
    {"filter": "@< 3 hrs", "weight": 8},
    {"filter": "@> 3 hrs", "weight": 10},
]


def main() -> None:
    config = {"TODOIST_DEV_USER_TOKEN": os.getenv("TODOIST_DEV_USER_TOKEN")}
    config = {key: value for key, value in config.items() if value is not None}

    api = TodoistAPIAsync(config["TODOIST_DEV_USER_TOKEN"])

    asyncio.run(
        reschedule(
            api=api,
            filter="!assigned to:others & !no date & !recurring & no deadline & !p1",
            max_weight=max_weight,
            rules=rules,
        )
    )

    asyncio.run(
        reschedule(
            api=api,
            filter="!assigned to:others & !no date & overdue & recurring & no deadline & !p1",
            max_weight=max_weight,
        )
    )
