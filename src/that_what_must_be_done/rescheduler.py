from datetime import date, datetime
from todoist_api_python.api_async import TodoistAPIAsync
from todoist_api_python.models import Task
from collections import defaultdict

max_weight = 10
rules = [
    {"filter": "@< 15 min", "limit": 4, "weight": 2},
    {"filter": "@< 60 min", "weight": 4},
    {"filter": "@< 3 hrs", "weight": 8},
    {"filter": "@> 3 hrs", "weight": 10},
]


async def reschedule(config: dict[str, str]) -> None:
    api = TodoistAPIAsync(config["TODOIST_DEV_USER_TOKEN"])

    try:
        tasks = await api.get_tasks(  # pyright: ignore[reportUnknownMemberType]
            filter="!assigned to:others & !no date & !recurring & !p1"
        )
    except Exception as error:
        print(error)
        tasks = []

    today = datetime.now().date()

    date_dict: dict[str, list[Task]] = defaultdict(list)
    for task in tasks:
        if task.due is not None:
            date_dict[task.due.date].append(task)

    # FIXME: Need to sort by the due date
    new_schedule: dict[str, list[Task]] = defaultdict(list)
    for bucket_date_str, tasks in date_dict.items():
        # Check if date is before today
        bucket_date = date.fromisoformat(bucket_date_str)
        if bucket_date < today:
            print("BEFORE TODAY")
            for task in tasks:
                print(task.content)
        elif bucket_date == today:
            print("TODAY")
            for task in tasks:
                print(task.content)
        else:
            print("AFTER TODAY")
            for task in tasks:
                print(task.content)
