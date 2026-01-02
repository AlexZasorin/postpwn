import asyncio
import logging
import os
import re
from asyncio import AbstractEventLoop
from datetime import date, datetime
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
from pydantic import ValidationError
from todoist_api_python.api_async import TodoistAPIAsync

from postpwn.api import TodoistAPIProtocol
from postpwn.rescheduler import reschedule
from postpwn.types import Rule, ScheduleConfig, WeightConfig
from postpwn.validation import CRON_SCHEDULE_REGEX

_ = load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RescheduleParams(TypedDict):
    filter: str
    rules: str | None
    dry_run: bool
    token: str | None
    time_zone: str
    schedule: str | None


async def run_schedule(
    api: TodoistAPIProtocol,
    max_weight: WeightConfig | int,
    filter: str,
    rules: list[Rule] | None,
    dry_run: bool,
    time_zone: str,
    schedule: str,
    curr_date: date | None = None,
) -> AsyncIOScheduler:
    logger.info(f"Running on schedule: {schedule}")
    scheduler = AsyncIOScheduler()

    async def reschedule_job():
        await reschedule(
            api=api,
            max_weight=max_weight,
            curr_date=curr_date,
            time_zone=time_zone,
            rules=rules,
            filter=filter,
            dry_run=dry_run,
        )

    _ = scheduler.add_job(  # pyright: ignore[reportUnknownMemberType]
        reschedule_job,
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
    default=None,
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
    loop = asyncio.get_event_loop()

    curr_date = datetime.now(tz=ZoneInfo(kwargs["time_zone"])).date()
    return postpwn(api, loop, curr_date, **kwargs)


def postpwn(
    api: TodoistAPIProtocol,
    loop: AbstractEventLoop,
    curr_date: date,
    **kwargs: Unpack[RescheduleParams],
) -> None:
    today = curr_date.date() if isinstance(curr_date, datetime) else curr_date

    if kwargs["rules"] and os.path.exists(kwargs["rules"]):
        logger.info(f"Loading rules from {kwargs['rules']}")
        try:
            with open(kwargs["rules"]) as f:
                schedule_config = ScheduleConfig.model_validate_json(f.read())
                max_weight = schedule_config.max_weight
                rules = schedule_config.rules
        except ValidationError as e:
            raise ValueError(
                f"Invalid rules file '{kwargs['rules']}': {e.error_count()} validation error(s) found.\n{e}"
            ) from e
    else:
        logger.info("No rules provided, using defaults.")
        max_weight = 10
        rules = None

    if rules:
        weight_limit = (
            max_weight
            if isinstance(max_weight, int)
            else max(max_weight.model_dump().values())
        )

        for rule in rules:
            if rule.get("weight", 0) > weight_limit:
                raise ValueError(
                    f"Invalid rule config: {rule['filter']} exceeds max weight {weight_limit}"
                )

    logger.info(f"Rules: {rules}")

    if kwargs["schedule"]:
        if not re.match(CRON_SCHEDULE_REGEX, kwargs["schedule"]):
            raise ValueError("Invalid cron schedule.")

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

    loop.run_until_complete(
        reschedule(
            api=api,
            max_weight=max_weight,
            time_zone=kwargs["time_zone"],
            curr_date=today,
            rules=rules,
            filter=kwargs["filter"],
            dry_run=kwargs["dry_run"],
        )
    )
