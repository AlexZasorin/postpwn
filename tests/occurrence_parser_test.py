# Manually verified against the Todoist UI (2026-08-12). These duration
# ("for N period") combinations are invalid:
#   - "every day for 2 hours"
#   - "every year for 2 hours"
#   - "every quarter for 2 hours"
# The rule is not "duration must match period" in general - mismatched
# non-hour combinations parse fine (e.g. "every year for 2 days",
# "every month for 2 days"). Only "hour"/"hours" as the duration word is
# restricted, and only unrestricted when the period itself is hour-based:
#   - "every hour for 2 hours" parses
#   - "every hour for 2 day" parses
#   - "every 2 hours for 1 day" parses
#   - "every 2 hours for 1 hour" parses
# Also: "quarter" never pluralizes to "quarters" in any context tested.

# Tests to add
# - midnight
# - specifics order

import logging
from datetime import datetime
from enum import Enum, auto
from typing import NotRequired, TypedDict
from zoneinfo import ZoneInfo

from lark import LexError, ParseError
import pytest

from postpwn.parser.occurrence_parser import todoist_parser

logger = logging.getLogger(__name__)

curr_datetime = datetime(2026, 7, 26, 6, 0, 0, tzinfo=ZoneInfo("US/Pacific"))


# FIXME: Only allow one DTSTART per RRuleSet
class RRule(TypedDict):
    RRULE: list[str]
    DTSTART: NotRequired[list[str]]


type RRuleSet = list[RRule]


class Unsupported(Enum):
    COMPLETION_BASED = auto()
    UNSUPPORTED_PERIOD = auto()


parse_test_data: list[tuple[str, bool]] = [
    ("every day", True),
    ("everyday", True),
    ("ev day", True),
    ("daily", True),
    ("every weekday", True),
    ("every workday", True),
    ("every week", True),
    ("weekly", True),
    ("every month", True),
    ("monthly", True),
    ("every year", True),
    ("yearly", True),
    ("everyday starting on aug 3", True),
    ("everyday from aug 3", True),
    ("everyday ending aug 3", True),
    ("everyday until aug 3", True),
    ("every Wednesday, Friday, Saturday ending Saturday", True),
    ("everyday for 3 weeks", True),
    ("everyday from 10 May until 20 May", True),
    ("every hour", True),
    ("every 12 hours starting at 9pm", True),
    ("every mon, fri at 20:00", True),
    ("every mon, fri at 2300", True),
    ("every last workday at 3pm", True),
    ("every fri at noon", True),
    ("every monday, friday", True),
    ("ev monday, friday", True),
    ("every mon, fri", True),
    ("every 2, 15, 27", True),
    ("ev 2, 15, 27", True),
    ("every 14 jan, 14 apr, 15 jun, 15 sep", True),
    ("every 15th workday, first workday, last workday", True),
    ("every 1st wed jan, 3rd thu jul", True),
    ("every 3 workday", True),
    ("every quarter", True),
    ("quarterly", True),
    ("every! 3 hours", True),
    ("every! 2 months", True),
    ("after 10 days", True),
    ("every other day", True),
    ("every other week", True),
    ("every other month", True),
    ("every other year", True),
    ("every other fri", True),
    ("new year day", True),
    ("valentine", True),
    ("Valentine's Day", True),
    ("halloween", True),
    ("new year eve", True),
]


def is_parseable(due_string: str) -> bool:
    try:
        logger.error(
            f"due_string: {due_string}\nparse tree{todoist_parser.parse(due_string)}",  # pyright: ignore[reportUnknownMemberType]
        )
        return True
    except (ParseError, LexError) as e:
        print(e)
        return False


@pytest.mark.parametrize("due_string,expected", parse_test_data)
def test_parse_todoist_to_rrule(due_string: str, expected: bool):
    assert is_parseable(due_string) == expected


# we will assuming floating times for this test set, and non-floating times in another
compile_test_data: list[tuple[str, RRule | RRuleSet | Unsupported]] = [
    ("every day", {"RRULE": ["FREQ=DAILY"]}),
    ("everyday", {"RRULE": ["FREQ=DAILY"]}),
    ("ev day", {"RRULE": ["FREQ=DAILY"]}),
    ("daily", {"RRULE": ["FREQ=DAILY"]}),
    ("every weekday", {"RRULE": ["FREQ=WEEKLY", "BYDAY=MO,TU,WE,TH,FR"]}),
    ("every workday", {"RRULE": ["FREQ=WEEKLY", "BYDAY=MO,TU,WE,TH,FR"]}),
    ("every week", {"RRULE": ["FREQ=WEEKLY"]}),
    ("weekly", {"RRULE": ["FREQ=WEEKLY"]}),
    ("every month", {"RRULE": ["FREQ=MONTHLY"]}),
    ("monthly", {"RRULE": ["FREQ=MONTHLY"]}),
    ("every year", {"RRULE": ["FREQ=YEARLY"]}),
    ("yearly", {"RRULE": ["FREQ=YEARLY"]}),
    (
        "everyday starting on aug 3",
        {
            "DTSTART": ["VALUE=DATE:20260803"],
            "RRULE": ["FREQ=DAILY"],
        },
    ),
    (
        "everyday from aug 3",
        {
            "DTSTART": ["VALUE=DATE:20260803"],
            "RRULE": ["FREQ=DAILY"],
        },
    ),
    (
        "everyday ending aug 3",
        {
            "RRULE": ["FREQ=DAILY", "UNTIL=20260803"],
        },
    ),
    (
        "everyday until aug 3",
        {
            "RRULE": ["FREQ=DAILY", "UNTIL=20260803"],
        },
    ),
    (
        "every Wednesday, Friday, Saturday ending Saturday",
        {"RRULE": ["FREQ=WEEKLY", "BYDAY=WE,FR,SA", "UNTIL=20260801"]},
    ),
    # NOTE: "UNTIL" is inclusive
    ("everyday for 3 weeks", {"RRULE": ["FREQ=DAILY", "UNTIL=20260815"]}),
    (
        "everyday from 10 May until 20 May",
        {"DTSTART": ["VALUE=DATE:20270510"], "RRULE": ["FREQ=DAILY", "UNTIL=20270520"]},
    ),
    ("every hour", {"RRULE": ["FREQ=HOURLY"]}),
    (
        "every 12 hours starting at 9pm",
        {
            "DTSTART": ["20260726T210000"],
            "RRULE": ["FREQ=HOURLY", "INTERVAL=12"],
        },
    ),
    (
        "every mon, fri at 20:00",
        {
            "DTSTART": ["20260727T200000"],
            "RRULE": ["FREQ=WEEKLY", "BYDAY=MO,FR"],
        },
    ),
    (
        "every last workday at 3pm",
        {
            "DTSTART": ["20260731T150000"],
            "RRULE": ["FREQ=MONTHLY", "BYDAY=MO,TU,WE,TH,FR", "BYSETPOS=-1"],
        },
    ),
    (
        "every fri at noon",
        {"DTSTART": ["20260731T120000"], "RRULE": ["FREQ=WEEKLY", "BYDAY=FR"]},
    ),
    ("every monday, friday", {"RRULE": ["FREQ=WEEKLY", "BYDAY=MO,FR"]}),
    ("ev monday, friday", {"RRULE": ["FREQ=WEEKLY", "BYDAY=MO,FR"]}),
    ("every mon, fri", {"RRULE": ["FREQ=WEEKLY", "BYDAY=MO,FR"]}),
    ("every 2, 15, 27", {"RRULE": ["FREQ=MONTHLY", "BYMONTHDAY=2,15,27"]}),
    ("ev 2, 15, 27", {"RRULE": ["FREQ=MONTHLY", "BYMONTHDAY=2,15,27"]}),
    (
        "every 14 jan, 14 apr, 15 jun, 15 sep",
        [
            {"RRULE": ["FREQ=YEARLY", "BYMONTH=1", "BYMONTHDAY=14"]},
            {"RRULE": ["FREQ=YEARLY", "BYMONTH=4", "BYMONTHDAY=14"]},
            {"RRULE": ["FREQ=YEARLY", "BYMONTH=6", "BYMONTHDAY=15"]},
            {"RRULE": ["FREQ=YEARLY", "BYMONTH=9", "BYMONTHDAY=15"]},
        ],
    ),
    (
        "every 15th workday, first workday, last workday",
        {"RRULE": ["FREQ=MONTHLY", "BYDAY=MO,TU,WE,TH,FR", "BYSETPOS=1,15,-1"]},
    ),
    (
        "every 1st wed jan, 3rd thu jul",
        [
            {"RRULE": ["FREQ=YEARLY", "BYMONTH=1", "BYDAY=WE", "BYSETPOS=1"]},
            {"RRULE": ["FREQ=YEARLY", "BYMONTH=7", "BYDAY=TH", "BYSETPOS=3"]},
        ],
    ),
    ("every 3 workday", Unsupported.UNSUPPORTED_PERIOD),
    (
        "every quarter",
        {"DTSTART": ["VALUE=DATE:20260726"], "RRULE": ["FREQ=MONTHLY", "INTERVAL=3"]},
    ),
    (
        "quarterly",
        {"DTSTART": ["VALUE=DATE:20260726"], "RRULE": ["FREQ=MONTHLY", "INTERVAL=3"]},
    ),
    ("every! 3 hours", Unsupported.COMPLETION_BASED),
    ("every! 2 months", Unsupported.COMPLETION_BASED),
    ("after 10 days", Unsupported.COMPLETION_BASED),
    (
        "every other day",
        {"DTSTART": ["VALUE=DATE:20260726"], "RRULE": ["FREQ=DAILY", "INTERVAL=2"]},
    ),
    (
        "every other week",
        {"DTSTART": ["VALUE=DATE:20260726"], "RRULE": ["FREQ=WEEKLY", "INTERVAL=2"]},
    ),
    (
        "every other month",
        {"DTSTART": ["VALUE=DATE:20260726"], "RRULE": ["FREQ=MONTHLY", "INTERVAL=2"]},
    ),
    (
        "every other year",
        {"DTSTART": ["VALUE=DATE:20260726"], "RRULE": ["FREQ=YEARLY", "INTERVAL=2"]},
    ),
    (
        "every other fri",
        {
            "DTSTART": ["VALUE=DATE:20260731"],
            "RRULE": ["FREQ=WEEKLY", "BYDAY=FR", "INTERVAL=2"],
        },
    ),
    ("new year day", {"DTSTART": ["VALUE=DATE:20270101"], "RRULE": ["FREQ=YEARLY"]}),
    ("valentine", {"DTSTART": ["VALUE=DATE:20270214"], "RRULE": ["FREQ=YEARLY"]}),
    ("Valentine's Day", {"DTSTART": ["VALUE=DATE:20270214"], "RRULE": ["FREQ=YEARLY"]}),
    ("halloween", {"DTSTART": ["VALUE=DATE:20261031"], "RRULE": ["FREQ=YEARLY"]}),
    ("new year eve", {"DTSTART": ["VALUE=DATE:20261231"], "RRULE": ["FREQ=YEARLY"]}),
]


@pytest.mark.parametrize("due_string,expected", compile_test_data)
def test_compile_todoist_to_rrule(
    due_string: str, expected: RRule | RRuleSet | Unsupported
):
    pass
