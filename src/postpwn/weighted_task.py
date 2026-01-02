from dataclasses import dataclass
from todoist_api_python.models import Task


@dataclass(eq=True, order=True)
class WeightedTask(Task):
    weight: int = 1

    def __init__(self, task: Task, weight: int):
        super().__init__(  # pyright: ignore[reportUnknownMemberType]
            id=task.id,
            content=task.content,
            description=task.description,
            project_id=task.project_id,
            section_id=task.section_id,
            parent_id=task.parent_id,
            labels=task.labels,
            priority=task.priority,
            due=task.due,
            deadline=task.deadline,
            duration=task.duration,
            is_collapsed=task.is_collapsed,
            order=task.order,
            assignee_id=task.assignee_id,
            assigner_id=task.assigner_id,
            completed_at=task.completed_at,  # pyright: ignore[reportUnknownMemberType]
            creator_id=task.creator_id,
            created_at=task.created_at,  # pyright: ignore[reportUnknownMemberType]
            updated_at=task.updated_at,  # pyright: ignore[reportUnknownMemberType]
        )

        self.weight = weight
