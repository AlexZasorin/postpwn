from typing import NotRequired, Required, TypedDict


class Rule(TypedDict, total=False):
    filter: Required[str]
    limit: int
    weight: int


class UpdateTaskParams(TypedDict):
    content: NotRequired[str]
    description: NotRequired[str]
    labels: NotRequired[list[str]]
    priority: NotRequired[int]
    due_string: NotRequired[str]
    due_date: NotRequired[str]
    due_datetime: NotRequired[str]
    due_lang: NotRequired[str]
    assignee_id: NotRequired[str]
    duration: NotRequired[int]
    duration_unit: NotRequired[str]
