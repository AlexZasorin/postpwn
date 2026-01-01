import logging
from .cli import cli

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(name)s [%(levelname)s]: %(message)s"
)


def main() -> None:
    cli()
