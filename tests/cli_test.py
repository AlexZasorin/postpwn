import logging
from datetime import datetime

import pytest
from helpers.data_generators import build_task
from helpers.fake_api import FakeTodoistAPI

from postpwn.cli import run_schedule


logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_schedule_registers_job_and_executes() -> None:
    """when schedule is provided, it registers a job with correct cron trigger and executes reschedule"""

    fake_api = FakeTodoistAPI("VALID_TOKEN")
    task = build_task()
    fake_api.setup_tasks([task])

    curr_date = datetime(2025, 1, 5, 0, 0, 0).date()
    cron_schedule = "0 0 * * *"  # Midnight daily

    # Start scheduler
    scheduler = await run_schedule(
        api=fake_api,
        max_weight=10,
        filter="test",
        rules=None,
        dry_run=False,
        time_zone="UTC",
        schedule=cron_schedule,
        curr_date=curr_date,
    )

    try:
        # Verify job was scheduled
        jobs = scheduler.get_jobs()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        assert len(jobs) == 1  # pyright: ignore[reportUnknownArgumentType]

        job = jobs[0]  # pyright: ignore[reportUnknownVariableType]

        # Verify cron trigger configuration
        trigger_str = str(job.trigger)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        assert "hour='0'" in trigger_str
        assert "minute='0'" in trigger_str
        assert job.trigger.timezone.key == "UTC"  # pyright: ignore[reportUnknownMemberType]

        # Manually trigger the job to verify it executes
        await job.func()  # pyright: ignore[reportUnknownMemberType]

        # Verify the reschedule logic actually ran
        assert fake_api.update_task.call_count == 1
        assert fake_api.update_task.call_args.kwargs["due_date"] == curr_date

    finally:
        # Cleanup
        scheduler.shutdown()
