from datetime import date, datetime
import logging
from typing import (
    Annotated,
    AsyncGenerator,
    Literal,
    NotRequired,
    Protocol,
    TypedDict,
)
from annotated_types import Ge, Le, MaxLen, MinLen
from todoist_api_python.api import LanguageCode
from todoist_api_python.models import Task


class GetTasksInput(TypedDict):
    project_id: NotRequired[str]
    section_id: NotRequired[str]
    parent_id: NotRequired[str]
    label: NotRequired[str]
    ids: NotRequired[list[str]]
    limit: NotRequired[Annotated[int, Ge(1), Le(200)]]


class FilterTasksInput(TypedDict):
    query: Annotated[str, MaxLen(1024)] | None
    lang: str | None
    limit: Annotated[int, Ge(1), Le(200)] | None


class UpdateTaskInput(TypedDict):
    content: NotRequired[Annotated[str, MinLen(1), MaxLen(500)]]
    description: NotRequired[Annotated[str, MaxLen(16383)]]
    labels: NotRequired[list[Annotated[str, MaxLen(60)]]]
    priority: NotRequired[Annotated[int, Ge(1), Le(4)]]
    due_string: NotRequired[Annotated[str, MaxLen(150)]]
    due_lang: NotRequired[LanguageCode]
    due_date: NotRequired[date]
    due_datetime: NotRequired[datetime]
    assignee_id: NotRequired[str]
    day_order: NotRequired[int]
    collapsed: NotRequired[bool]
    duration: NotRequired[Annotated[int, Ge(1)]]
    duration_unit: NotRequired[Literal["minute", "day"]]
    deadline_date: NotRequired[date]
    deadline_lang: NotRequired[LanguageCode]


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TodoistAPIProtocol(Protocol):
    async def filter_tasks(
        self,
        *,
        query: Annotated[str, MaxLen(1024)] | None = None,
        lang: str | None = None,
        limit: Annotated[int, Ge(1), Le(200)] | None = None,
    ) -> AsyncGenerator[list[Task], None]: ...

    async def update_task(
        self,
        task_id: str,
        *,
        content: Annotated[str, MinLen(1), MaxLen(500)] | None = None,
        description: Annotated[str, MaxLen(16383)] | None = None,
        labels: list[Annotated[str, MaxLen(60)]] | None = None,
        priority: Annotated[int, Ge(1), Le(4)] | None = None,
        due_string: Annotated[str, MaxLen(150)] | None = None,
        due_lang: LanguageCode | None = None,
        due_date: date | None = None,
        due_datetime: datetime | None = None,
        assignee_id: str | None = None,
        day_order: int | None = None,
        collapsed: bool | None = None,
        duration: Annotated[int, Ge(1)] | None = None,
        duration_unit: Literal["minute", "day"] | None = None,
        deadline_date: date | None = None,
        deadline_lang: LanguageCode | None = None,
    ) -> Task: ...
