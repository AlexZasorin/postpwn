# Postpwn

A smart task rescheduler for Todoist that optimally distributes your tasks
based on rules you set.

## Features

- Supports custom rules based on task labels
- Reschedules tasks based on customizable weight limits
- Can run as a one-off command or on a schedule

## Usage

Currently the best way to use this project is through the docker image
published to GHCR. Eventually, a Python package and standalone binary will be
provided.

Keep in mind that this is still in development and the API is subject to
change. I recommend pinning the version/SHA of the image you use until I get
around to adding tests and proper versioning.

Example docker-compose file:

```yaml
services:
  reschedule-tasks:
    init: true
    image: ghcr.io/alexzasorin/postpwn/app:latest
    command:
      [
        # Reschedule tasks that are not assigned to others, have a date, are not
        # recurring, have no deadline, and are not highest priority
        "--filter",
        "!assigned to:others & !no date & !recurring & no deadline & !p1",
        # Path to JSON rules file inside the container
        "--rules",
        "/app/rules.json",
        # Time zone for scheduling
        "--time-zone",
        "US/Pacific",
        # Cron string to run this at midnight every day 
        "--schedule",
        "0 0 * * *",
        # Your Todoist API token
        "--token",
        "${TODOIST_USER_TOKEN}",
      ]
    volumes:
      # Mount your rules file into the container
      - ~/.config/rescheduler/rules.json:/app/rules.json
  reschedule-recurring:
    init: true
    image: ghcr.io/alexzasorin/postpwn/app:latest
    container_name: reschedule-recurring
    command:
      [
        # Reschedule tasks that are not assigned to others, have a date, are overdue,
        # are recurring, have no deadline, and are not highest priority
        "--filter",
        "!assigned to:others & !no date & overdue & recurring & no deadline & !p1",
        "--time-zone",
        "US/Pacific",
        "--schedule",
        "0 0 * * *",
        "--token",
        "${TODOIST_USER_TOKEN}",
      ]
    volumes:
      - ~/.config/rescheduler/rules.json:/app/rules.json
```

## Options

- `--filter`: Todoist filter to select tasks (default: "!assigned to:others &
!no date & !recurring & no deadline")
- `--rules`: Path to JSON rules file
- `--dry-run`: Simulate changes without applying them
- `--token`: Todoist API token (can also be set via TODOIST_USER_TOKEN
environment variable)
- `--time-zone`: Time zone for scheduling (default: "Etc/UTC")
- `--schedule`: Cron string for running on a schedule

## Configuration

### Rules File

Weights can be assigned to tasks based on their labels. The rescheduler will
optimally distribute tasks based on these weights, with higher priority tasks
being valued more.

Create a JSON file to define weights for different task labels and daily
capacity:

```jsonc
{
  // Maximum weight of tasks allowed per day.
  "max_weight": 10,
  // Alternatively, you can set different weights for each day
  // "max_weight": {
  //   "sunday": 5,
  //   "monday": 10,
  //   "tuesday": 10,
  //   "wednesday": 10,
  //   "thursday": 10,
  //   "friday": 8,
  //   "saturday": 5
  // },
  "rules": [
    // filter - Todoist task label
    // weight - Weight of the task with this label
    { "filter": "@< 15 min", "weight": 2 },
    { "filter": "@< 60 min", "weight": 4 },
    { "filter": "@< 3 hrs", "weight": 8 },
    { "filter": "@> 3 hrs", "weight": 10 },
  ],
}
```

## TODO

- [ ] Add tests
  - [ ] Refactor FakeTodoistAPI to create "distribution" of final task
  dates for easier comparison, refactor test cases to use this
  - [ ] Test that priority tasks are scheduled earlier
  - [ ] Retry test
  - [ ] Test cron scheduling
  - [ ] Timezone test
- [ ] Make logs not look like ass lol
- [ ] Switch to toml config???
  - [ ] Merge CLI args and rules config into a unified configuration
- [ ] Allow disabling "smart" rescheduling
- [ ] Use Session from requests to implement retry logic?
- [ ] Catch improper cron string
- [ ] Try using V4 API of scheduler for typing
- [ ] Add limits as alternative to weights
- [ ] Add semantic release
- [ ] Publish executable using PyInstaller
- [ ] Add value to WeightedTask and increase value for older tasks, make
optional
- [ ] Allow overriding the default values for each priority
- [ ] Move my deployment out of the main code
- [ ] Allow "punting" of tasks further than today

## License

GPL-3.0 License
