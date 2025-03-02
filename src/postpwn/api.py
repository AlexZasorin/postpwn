from typing import Protocol

from requests import HTTPError, Session
from todoist_api_python.models import Due, Duration, Task


class TodoistAPIProtocol(Protocol):
    async def get_tasks(self, **kwargs: object) -> list[Task]: ...
    async def update_task(self, task_id: str, **kwargs: object) -> bool: ...


class FakeTodoistAPI:
    def __init__(self, token: str, _: Session | None = None):
        self.token: str = token

    async def get_tasks(self, **kwargs: object) -> list[Task]:
        if self.token != "VALID_TOKEN":
            raise HTTPError("401 Client Error: Unauthorized for url: idk")

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

    async def update_task(self, task_id: str, **kwargs: object) -> bool:
        return True
