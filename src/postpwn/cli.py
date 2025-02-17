import asyncio
import logging
import os
import sys
from functools import partial
from typing import TypedDict, Unpack
from zoneinfo import ZoneInfo

import click
from apscheduler.schedulers.asyncio import (  # pyright: ignore[reportMissingTypeStubs]
    AsyncIOScheduler,
)
from apscheduler.triggers.cron import (  # pyright: ignore[reportMissingTypeStubs]
    CronTrigger,
)
from dotenv import load_dotenv
from todoist_api_python.api_async import TodoistAPIAsync

from postpwn.rescheduler import reschedule
from postpwn.types import Rule, ScheduleConfig, WeightConfig

_ = load_dotenv()

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RescheduleParams(TypedDict):
    filter: str
    rules: str | None
    dry_run: bool
    token: str | None
    time_zone: str
    schedule: str | None


async def run_schedule(
    api: TodoistAPIAsync,
    max_weight: WeightConfig | int,
    filter: str,
    rules: list[Rule] | None,
    dry_run: bool,
    time_zone: str,
    schedule: str,
) -> AsyncIOScheduler:
    logger.info(f"Running on schedule: {schedule}")
    scheduler = AsyncIOScheduler()
    job = partial(
        reschedule,
        api=api,
        max_weight=max_weight,
        rules=rules,
        filter=filter,
        dry_run=dry_run,
        time_zone=time_zone,
    )

    _ = scheduler.add_job(  # pyright: ignore[reportUnknownMemberType]
        job,
        CronTrigger.from_crontab(  # pyright: ignore[reportUnknownMemberType]
            schedule, timezone=ZoneInfo(time_zone)
        ),
    )

    scheduler.start()

    return scheduler


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
@click.option(
    "--schedule",
    help="Cron schedule for rescheduling to run on a cadence.",
    default=None,
    type=str,
)
def cli(**kwargs: Unpack[RescheduleParams]) -> None:
    logger.debug(kwargs)
    api = TodoistAPIAsync(kwargs["token"] if kwargs["token"] else "")

    if kwargs["rules"] and os.path.exists(kwargs["rules"]):
        logger.info(f"Loading rules from {kwargs['rules']}")
        with open(kwargs["rules"]) as f:
            schedule_config = ScheduleConfig.model_validate_json(f.read())
            max_weight = schedule_config.max_weight
            rules = schedule_config.rules
    else:
        logger.info("No rules provided, using defaults.")
        max_weight = 10
        rules = None

    logger.info(f"Rules: {rules}")

    if kwargs["schedule"]:
        loop = asyncio.get_event_loop()
        schedule = loop.run_until_complete(
            run_schedule(
                api=api,
                max_weight=max_weight,
                rules=rules,
                filter=kwargs["filter"],
                dry_run=kwargs["dry_run"],
                time_zone=kwargs["time_zone"],
                schedule=kwargs["schedule"],
            )
        )
        try:
            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            schedule.shutdown()
            loop.close()
        return

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
