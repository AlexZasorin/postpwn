import asyncio
import os
from typing import TypedDict, Unpack
import click

from dotenv import load_dotenv
from todoist_api_python.api_async import TodoistAPIAsync

from that_what_must_be_done.rescheduler import reschedule
from that_what_must_be_done.types import ScheduleConfig

_ = load_dotenv()


class RescheduleParams(TypedDict):
    filter: str
    rules: str
    dry_run: bool
    token: str | None
    time_zone: str


@click.command(
    help="Optimally reschedules your tasks according to your filters and rules."
)
@click.option(
    "--filter",
    help="Todoist filter to select tasks to reschedule.",
    default="!assigned to:others & !no date & !recurring & no deadline",
    show_default=True,
    type=str,
)
@click.option(
    "--rules",
    help="Path to JSON file containing rules for rescheduling.",
    default="rules.json",
    show_default=True,
    type=click.Path(),
)
@click.option(
    "--dry-run",
    help="Simulate rescheduling without making changes.",
    default=False,
    show_default=True,
    is_flag=True,
    type=bool,
)
@click.option(
    "--token",
    help="Todoist API key. Fetched from TODOIST_",
    default=os.getenv("TODOIST_USER_TOKEN"),
    type=str,
)
@click.option(
    "--time-zone",
    help="Time zone identifier for rescheduling.",
    default="Etc/UTC",
    show_default=True,
    type=str,
)
def cli(**kwargs: Unpack[RescheduleParams]) -> None:
    api = TodoistAPIAsync(kwargs["token"] if kwargs["token"] else "")

    if os.path.exists(kwargs["rules"]):
        with open(kwargs["rules"]) as f:
            schedule_config = ScheduleConfig.model_validate_json(f.read())
            max_weight = schedule_config.max_weight
            rules = schedule_config.rules
    else:
        max_weight = 10
        rules = []

    print(rules)

    asyncio.run(
        reschedule(
            api=api,
            max_weight=max_weight,
            rules=rules,
            filter=kwargs["filter"],
            dry_run=kwargs["dry_run"],
            time_zone=kwargs["time_zone"],
        )
    )
