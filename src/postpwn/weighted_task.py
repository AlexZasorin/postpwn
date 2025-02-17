from dataclasses import dataclass
from todoist_api_python.models import Task


@dataclass(eq=True, order=True)
class WeightedTask(Task):
    weight: int = 1

    def __init__(self, task: Task, weight: int):
        super().__init__(
            assignee_id=task.assignee_id,
            assigner_id=task.assigner_id,
            comment_count=task.comment_count,
            is_completed=task.is_completed,
            content=task.content,
            created_at=task.created_at,
            creator_id=task.creator_id,
            description=task.description,
            due=task.due,
            id=task.id,
            labels=task.labels,
            order=task.order,
            parent_id=task.parent_id,
            priority=task.priority,
            project_id=task.project_id,
            section_id=task.section_id,
            url=task.url,
            duration=task.duration,
            sync_id=task.sync_id,
        )
        self.weight = weight
