import asyncio
from functools import partial
import os
from typing import TypedDict, Unpack
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # pyright: ignore[reportMissingTypeStubs]
from apscheduler.triggers.cron import CronTrigger  # pyright: ignore[reportMissingTypeStubs]
import click
from dotenv import load_dotenv
from todoist_api_python.api_async import TodoistAPIAsync

from that_what_must_be_done.rescheduler import reschedule
from that_what_must_be_done.types import Rule, ScheduleConfig, WeightConfig

_ = load_dotenv()


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
    rules: list[Rule],
    dry_run: bool,
    time_zone: str,
    schedule: str,
) -> None:
    print(f"Running on schedule: {schedule}")
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

    # I have to sleep here, otherwise the program will exit despite the scheduler/coroutines running
    while True:
        await asyncio.sleep(1000)


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
    print(kwargs)
    api = TodoistAPIAsync(kwargs["token"] if kwargs["token"] else "")

    if kwargs["rules"] and os.path.exists(kwargs["rules"]):
        with open(kwargs["rules"]) as f:
            schedule_config = ScheduleConfig.model_validate_json(f.read())
            max_weight = schedule_config.max_weight
            rules = schedule_config.rules
    else:
        max_weight = 10
        rules = []

    print(rules)

    if kwargs["schedule"]:
        try:
            asyncio.run(
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
        except (KeyboardInterrupt, SystemExit):
            pass
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
