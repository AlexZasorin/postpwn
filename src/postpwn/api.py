from typing import Optional, Protocol, TypedDict
from unittest.mock import AsyncMock

from requests import HTTPError, Session
from todoist_api_python.models import Due, Duration, Task


class GetTasksInput(TypedDict):
    project_id: Optional[str]
    section_id: Optional[str]
    label: Optional[str]
    filter: Optional[str]
    lang: Optional[str]
    ids: Optional[list[int]]


class UpdateTaskInput(TypedDict):
    content: Optional[str]
    description: Optional[str]
    labels: Optional[list[str]]
    priority: Optional[int]
    due_string: Optional[str]
    due_date: Optional[str]
    due_datetime: Optional[str]
    due_lang: Optional[str]
    assignee_id: Optional[int]
    duration: Optional[int]
    duration_unit: Optional[str]
    deadline_date: Optional[str]
    deadline_lang: Optional[str]


class TodoistAPIProtocol(Protocol):
    async def get_tasks(self, **kwargs: GetTasksInput) -> list[Task]: ...
    async def update_task(self, task_id: str, **kwargs: UpdateTaskInput) -> bool: ...


class FakeTodoistAPI:
    def __init__(self, token: str, _: Session | None = None):
        self.token: str = token

    async def get_tasks(self, **kwargs: object) -> list[Task]:
        if self.token != "VALID_TOKEN":
            raise HTTPError("401 Client Error: Unauthorized for url: idk")

        if kwargs["filter"] == "":
            return []

        return [
            Task(
                creator_id="2671355",
                created_at="2019-12-11T22:36:50",
                assignee_id="2671362",
                assigner_id="2671355",
                comment_count=10,
                is_completed=False,
                content="Buy Milk",
                description="",
                due=Due(
                    date="2016-09-01",
                    is_recurring=False,
                    datetime="2016-09-01T12:00:00",
                    string="tomorrow at 12",
                    timezone="Europe/Moscow",
                ),
                duration=Duration(amount=15, unit="minute"),
                id="2995104339",
                labels=["Food", "Shopping"],
                order=1,
                priority=1,
                project_id="2203306141",
                section_id="7025",
                parent_id="2995104589",
                url="https://todoist.com/showTask?id=2995104339",
            )
        ]

    update_task = AsyncMock(return_value=True)
