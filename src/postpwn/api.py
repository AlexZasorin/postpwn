from typing import NotRequired, Protocol, TypedDict, Unpack
from unittest.mock import AsyncMock

from requests import HTTPError, Session
from todoist_api_python.models import Due, Duration, Task


class GetTasksInput(TypedDict):
    project_id: NotRequired[str]
    section_id: NotRequired[str]
    label: NotRequired[str]
    filter: NotRequired[str]
    lang: NotRequired[str]
    ids: NotRequired[list[int]]


class UpdateTaskInput(TypedDict):
    content: NotRequired[str]
    description: NotRequired[str]
    labels: NotRequired[list[str]]
    priority: NotRequired[int]
    due_string: NotRequired[str]
    due_date: NotRequired[str]
    due_datetime: NotRequired[str]
    due_lang: NotRequired[str]
    assignee_id: NotRequired[int]
    duration: NotRequired[int]
    duration_unit: NotRequired[str]
    deadline_date: NotRequired[str]
    deadline_lang: NotRequired[str]


class TodoistAPIProtocol(Protocol):
    async def get_tasks(self, **kwargs: Unpack[GetTasksInput]) -> list[Task]: ...
    async def update_task(
        self, task_id: str, **kwargs: Unpack[UpdateTaskInput]
    ) -> bool: ...


class FakeTodoistAPI:
    def __init__(self, token: str, _: Session | None = None):
        self.token: str = token
        self.tasks: list[Task] = []

    def setup_tasks(self, tasks: list[Task]) -> None:
        self.tasks.extend(tasks)

    async def get_tasks(self, **kwargs: object) -> list[Task]:
        if self.token != "VALID_TOKEN":
            raise HTTPError("401 Client Error: Unauthorized for url: idk")

        if kwargs["filter"] == "":
            return []

        return self.tasks

    update_task = AsyncMock(return_value=True)
