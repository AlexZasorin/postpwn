from collections import defaultdict
from datetime import datetime
from typing import Annotated, AsyncGenerator
from unittest.mock import AsyncMock

from annotated_types import Ge, Le, MaxLen
from requests import HTTPError, Session
from todoist_api_python.models import Task

from helpers.data_generators import build_task


async def create_task_generator(
    tasks: list[Task], empty_query: bool = False
) -> AsyncGenerator[list[Task], None]:
    if empty_query:
        yield []
        return

    yield tasks


class FakeTodoistAPI:
    def __init__(self, token: str, _: Session | None = None):
        self.token: str = token
        self.tasks: list[Task] = []
        self.update_task = AsyncMock(
            return_value=build_task({"id": "mock_id", "content": "Updated Task"})
        )

    def setup_tasks(self, tasks: list[Task]) -> None:
        self.tasks.extend(tasks)

    def get_distribution(self) -> dict[datetime, dict[str, int]]:
        scheduled_dates: dict[datetime, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for call in self.update_task.call_args_list:
            task_id = call.args[0]
            due_datetime = (
                call.kwargs["due_datetime"]
                if "due_datetime" in call.kwargs
                else datetime.combine(call.kwargs["due_date"], datetime.min.time())
            )

            matching_task = next(t for t in self.tasks if t.id == task_id)
            task_label = (
                next(label for label in matching_task.labels)
                if matching_task.labels
                else None
            )

            if task_label:
                scheduled_dates[due_datetime][task_label] += 1

        return scheduled_dates

    async def filter_tasks(
        self,
        *,
        query: Annotated[str, MaxLen(1024)] | None = None,
        lang: str | None = None,
        limit: Annotated[int, Ge(1), Le(200)] | None = None,
    ) -> AsyncGenerator[list[Task], None]:
        if self.token != "VALID_TOKEN":
            raise HTTPError("401 Client Error: Unauthorized for url: idk")

        empty_query = query == ""
        return create_task_generator(self.tasks, empty_query)
