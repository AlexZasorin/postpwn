from .cli import cli

# def main() -> None:
#     config = {
#         "TODOIST_USER_TOKEN": os.getenv("TODOIST_USER_TOKEN"),
#         "CONFIG_PATH": os.getenv("CONFIG_PATH"),
#     }
#     config = {key: value for key, value in config.items() if value is not None}
#
#     api = TodoistAPIAsync(config["TODOIST_USER_TOKEN"])
#
#     config_path = f"{config['CONFIG_PATH']}"
#     if os.path.exists(config_path):
#         with open(config_path) as f:
#             schedule_config = ScheduleConfig.model_validate_json(f.read())
#             max_weight = schedule_config.max_weight
#             rules = schedule_config.rules
#     else:
#         max_weight = 10
#         rules = []
#
#     print(rules)
#
#     asyncio.run(
#         reschedule(
#             api=api,
#             filter="!assigned to:others & !no date & !recurring & no deadline & !p1",
#             max_weight=max_weight,
#             rules=rules,
#             time_zone="US/Pacific",
#         )
#     )
#
#     asyncio.run(
#         reschedule(
#             api=api,
#             filter="!assigned to:others & !no date & overdue & recurring & no deadline & !p1",
#             max_weight=max_weight,
#             time_zone="US/Pacific",
#         )
#     )
