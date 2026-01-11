from collections import defaultdict
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock

from requests import HTTPError, Session
from todoist_api_python.models import Task

from helpers.data_generators import build_task

type TaskDistribution = dict[str, int]


async def create_task_generator(
    tasks: dict[str, list[Task]], filter: str, token: str
) -> AsyncGenerator[list[Task], None]:
    if token != "VALID_TOKEN":
        raise HTTPError("401 Client Error: Unauthorized for url: idk")

    if filter == "":
        yield []
    else:
        yield tasks[filter]


class FakeTodoistAPI:
    def __init__(self, token: str, _: Session | None = None):
        self._tasks_by_filter: dict[str, list[Task]] = defaultdict(list)
        self._all_tasks: list[Task] = []
        self._all_task_ids: set[str] = set()

        self.update_task = AsyncMock(
            return_value=build_task({"id": "mock_id", "content": "Updated Task"})
        )
        self.filter_tasks = AsyncMock(
            side_effect=lambda **kwargs: create_task_generator(  # pyright: ignore[reportUnknownLambdaType]
                self._tasks_by_filter,
                kwargs["query"],  # pyright: ignore[reportUnknownArgumentType]
                token,
            )
        )

    def setup_tasks(self, filter: str, tasks: list[Task]) -> None:
        self._tasks_by_filter[filter] = tasks

        for task in tasks:
            if task.id not in self._all_task_ids:
                self._all_task_ids.add(task.id)
                self._all_tasks.append(task)

    def task_distribution(
        self,
    ) -> dict[datetime, TaskDistribution]:
        scheduled_dates: dict[datetime, TaskDistribution] = defaultdict(
            lambda: defaultdict(int)
        )

        for call in self.update_task.call_args_list:
            task_id = call.args[0]
            due_datetime = (
                call.kwargs["due_datetime"]
                if "due_datetime" in call.kwargs
                else datetime.combine(call.kwargs["due_date"], datetime.min.time())
            )

            matching_task = next((t for t in self._all_tasks if t.id == task_id), None)
            if not matching_task:
                continue

            task_label = (
                next(label for label in matching_task.labels)
                if matching_task.labels
                else None
            )

            if task_label:
                scheduled_dates[due_datetime][task_label] += 1

            scheduled_dates[due_datetime][str(matching_task.priority)] += 1

        return scheduled_dates
