import logging
from .cli import cli

logging.basicConfig(
    level=logging.WARN,
    format="%(asctime)-10s %(name)-20s [%(levelname)-5s]: %(message)s",
)

logger = logging.getLogger("postpwn")
logger.setLevel(logging.INFO)


def main() -> None:
    cli()
