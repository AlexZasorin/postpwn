import asyncio

from dotenv import dotenv_values, load_dotenv
from that_what_must_be_done.rescheduler import reschedule

config = load_dotenv()


def main() -> None:
    config = dotenv_values()
    config = {key: value for key, value in config.items() if value is not None}

    asyncio.run(reschedule(config))
