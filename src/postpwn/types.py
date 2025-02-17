from pydantic import BaseModel
from typing import Required, TypedDict


class Rule(TypedDict, total=False):
    filter: Required[str]
    limit: int
    weight: int


class WeightConfig(BaseModel):
    sunday: int
    monday: int
    tuesday: int
    wednesday: int
    thursday: int
    friday: int
    saturday: int


class ScheduleConfig(BaseModel):
    max_weight: WeightConfig | int
    rules: list[Rule]


class UpdateTaskParams(TypedDict, total=False):
    content: str
    description: str
    labels: list[str]
    priority: int
    due_string: str
    due_date: str
    due_datetime: str
    due_lang: str
    assignee_id: str
    duration: int
    duration_unit: str
