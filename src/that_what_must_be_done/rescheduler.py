from todoist_api_python.api_async import TodoistAPIAsync


async def reschedule(config: dict[str, str]) -> None:
    api = TodoistAPIAsync(config["TODOIST_DEV_USER_TOKEN"])
    try:
        projects = await api.get_projects()
        print(projects)
    except Exception as error:
        print(error)
