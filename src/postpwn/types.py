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
