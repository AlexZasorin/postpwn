from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


class Rule(BaseModel):
    filter: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1),
        Field(description="Filter string for selecting tasks"),
    ]
    limit: int | None = Field(
        None, gt=0, description="Optional limit for number of tasks"
    )
    weight: int | None = Field(
        None, gt=0, description="Optional weight for task prioritization"
    )


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
