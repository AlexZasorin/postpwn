from lark import Lark

# every             12              hours       starting at 9pm
# EVERY->every      interval->INT   HOUR->hours

todoist_parser = Lark(
    r"""
    rule: EVERY (" " interval)? " " period (" " specifics)?
        | EVERY (" " interval)? " " HOUR (" " specifics_hour)?
        | EVERY (" " interval)? " " QUARTER (" " specifics)?
        | (EVERY " ")? PERIOD_ADVERB (" " specifics)?

    specifics: start (" " until)?
             | until (" " start)?
             | duration
             | scheduled_time

    specifics_hour: start_hour (" " until)?
                  | until (" " start_hour)?
                  | duration_hour

    !interval: "other"
             | INT

    start: ("starting on" | "from") " " date
    start_hour: ("start on" | "starting at" | "from") " " (date | time)

    until: ("ending" | "until") " " (date | DAY)

    duration: "for" " " INT " " period
    duration_hour: "for" " " INT " " (period | HOUR)

    date: MONTH " " (ordinal_days | INT)
        | (ordinal_days | INT) " " MONTH

    scheduled_time: "at" " " time

    time: INT
        | INT ("am" | "pm")
        | "noon"
        | "midnight"
        | military_time

    military_time.2: /((\d|2[0-3]):|([01]\d|2[0-3]):?)([0-5]\d)/

    ordinal_days: "1st" | "2nd" | "3rd" | INT "th"

    EVERY: "every"
         | "ev"

    HOUR: "hour" "s"?

    QUARTER: "quarter"

    PERIOD_ADVERB: "everyday"
                 | "daily"
                 | "weekly"
                 | "monthly"
                 | "quarterly"
                 | "yearly"

    period: "day" "s"?
          | "weekday" "s"?
          | "workday" "s"?
          | "week" "s"?
          | "month" "s"?
          | "quarter"
          | "year" "s"?
          | DAY (("," | ", " | " ")? DAY)*
    
    MONTH: "january"i
         | "jan"i
         | "february"i
         | "feb"i
         | "march"i
         | "mar"i
         | "april"i
         | "apr"i
         | "may"i
         | "june"i
         | "jun"i
         | "july"i
         | "jul"i
         | "august"i
         | "aug"i
         | "september"i
         | "sept"i
         | "october"i
         | "oct"i
         | "november"i
         | "nov"i
         | "december"i
         | "dec"i

    DAY: "sunday"i
       | "sun"i
       | "monday"i
       | "mon"i
       | "tuesday"i
       | "tue"i
       | "wednesday"i
       | "wed"i
       | "thursday"i
       | "thurs"i
       | "thur"i
       | "thu"i
       | "friday"i
       | "fri"i
       | "saturday"i
       | "sat"i

    %import common.INT
""",
    start="rule",
)
