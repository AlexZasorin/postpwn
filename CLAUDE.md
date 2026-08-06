# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Your Role

This is a learning project. Your job is to help me understand things, not to
build them for me.

You do:

- Answer questions about the code, the domain, and the tools.
- Search the internet for documentation and libraries. Use Context7 first for
  library and framework docs. Use web search for everything else.
- Explain trade-offs between approaches so I can pick one.
- Point me at the part of the code or the doc page that holds the answer.

You do not:

- Write code for me.
- Give the answer directly.
- Refactor or "fix" things you notice along the way.

## The Socratic Method

Lead with questions, not conclusions. Ask what I expect to happen, what I have
already tried, and where my model of the system breaks. Let me reach the answer.

If I am stuck, narrow the question instead of answering it. Give a hint, then a
smaller hint. Reveal the answer only after I ask for it.

## The Override

When I explicitly ask for code or for a direct answer, give it. Phrases like
"just write it", "show me the code", or "tell me the answer" end the Socratic
mode for that request. Do not make me ask twice.

Read-only exploration is always allowed. Read files, run tests, and search the
web without asking.

## Project Overview

Postpwn is a smart task rescheduler for Todoist that optimally distributes tasks based on customizable rules and weight limits. It uses a knapsack algorithm to schedule tasks while respecting daily capacity constraints.

## Development Commands

### Environment Setup
```bash
# Uses uv for dependency management
uv sync  # Install dependencies
just setup-dotenv  # Set up environment variables
```

### Common Commands
```bash
just run [args]           # Run the CLI with optional arguments
just test                 # Run all tests with pytest
just lint                 # Run ruff linter
just format               # Format code with ruff
just check-formatting     # Check code formatting
just verify               # Run formatting, linting, and tests
```

### Running Tests
```bash
uv run pytest                    # Run all tests
uv run pytest tests/file_test.py # Run specific test file
uv run pytest -k "test_name"     # Run specific test by name
```

Tests use `pytest-spec` for readable output (configured in `pyproject.toml`).

### Type Checking
The project uses `basedpyright` in strict mode (see `pyproject.toml`).

## Development Workflow

### Test-Driven Development (TDD)

This project follows a **Red-Green-Refactor** strategy for all code changes.

**Important**: TDD is about the **development process**, not about writing simple or naive code. You can write sophisticated implementations and use powerful tools (like `unittest.mock.AsyncMock`) while still following TDD.

1. **Red**: Write a failing test first
   - Write a test for the behavior you want to implement
   - Use appropriate testing tools and patterns for the task
   - Run the test and verify it fails for the right reason
   - The test should fail because the functionality doesn't exist yet

2. **Green**: Implement the feature
   - Write code to make the test pass
   - The implementation can be as sophisticated as needed
   - Use best practices, clean abstractions, and appropriate libraries
   - Run the test and verify it passes

3. **Refactor**: Improve the code and tests
   - Clean up the implementation
   - Add more test cases for edge cases
   - Improve test quality (better mocks, clearer assertions, etc.)
   - Iterate: update tests → make them pass → refactor
   - Continue until the functionality and tests match the full specification

### Applying TDD Strategy to All Testing

**Follow the Red-Green-Refactor strategy even for quick manual tests:**
- If you plan to "just run the code and pass in some data" to verify behavior
- Run it first to see it fail (Red)
- Make your changes
- Run the same test again to see it pass (Green)
- Refactor as needed

**When doing manual/impromptu testing:**
- On a case-by-case basis, consider suggesting to convert it to a proper test case
- Benefits: permanent regression test, faster iteration with `pytest -k test_name`
- But don't assume formal tests are always required - follow the strategy regardless of format

### Example TDD Workflow

```python
# Step 1: RED - Write a failing test
def test_rule_validates_positive_weight():
    """when weight is negative, it raises a validation error"""
    with pytest.raises(ValidationError):
        Rule(filter="@test", weight=-5)

# Run: pytest -k test_rule_validates_positive_weight
# Expected: Test fails (Rule doesn't validate yet)

# Step 2: GREEN - Minimal implementation
class Rule(BaseModel):
    filter: str
    weight: int | None = Field(None, gt=0)  # Add gt=0 constraint

# Run: pytest -k test_rule_validates_positive_weight
# Expected: Test passes

# Step 3: REFACTOR - Add more cases, improve
def test_rule_validates_empty_filter():
    """when filter is empty, it raises a validation error"""
    with pytest.raises(ValidationError):
        Rule(filter="", weight=5)

# Iterate: Make new test pass, refactor, repeat
```

### Testing Best Practices

- Use the existing test helpers in `tests/helpers/`:
  - `FakeTodoistAPI` for mocking Todoist API calls
  - `build_task()` from `data_generators.py` for creating test tasks
  - Shared fixtures from `conftest.py` (loop, params, logging)
- Test files should mirror source structure: `src/postpwn/foo.py` → `tests/foo_test.py`
- Use descriptive docstrings: `"""when user provides invalid token, it raises HTTPError"""`
- Run specific tests during development: `pytest -k test_name` for fast feedback

## Architecture

### Core Components

1. **CLI Layer** (`cli.py`)
   - Entry point via Click commands
   - Handles argument parsing and validation
   - Manages both one-off execution and scheduled (cron) runs using APScheduler
   - Sets up the asyncio event loop and timezone handling

2. **Rescheduler** (`rescheduler.py`)
   - Contains the main `reschedule()` function that orchestrates the rescheduling logic
   - Uses `fill_my_sack()` - a 0/1 knapsack dynamic programming algorithm to optimally pack tasks into daily capacity limits
   - Implements retry logic with exponential backoff via Tenacity
   - Distributes tasks across future dates based on weight constraints

3. **API Layer** (`api.py`)
   - Defines `TodoistAPIProtocol` - a Protocol for Todoist API interactions
   - Allows for dependency injection and testing with fake implementations
   - Typed dictionaries for API inputs/outputs

4. **Data Models** (`types.py`, `weighted_task.py`)
   - `ScheduleConfig`: Pydantic model for JSON rules file
   - `WeightConfig`: Per-weekday weight limits or single integer
   - `Rule`: Pydantic model for filter/weight/limit definitions with validation
   - `WeightedTask`: Extends Todoist's Task model with weight field

### Key Algorithms

**Task Scheduling (fill_my_sack)**
- Classic 0/1 knapsack dynamic programming solution
- Maximizes total priority value while staying within weight limit
- Tasks with higher priority (p1=4, p2=3, p3=2, p4=1) are valued more
- Located in `rescheduler.py:52-72`

**Weight Adapter (weighted_adapter)**
- Converts raw Todoist tasks to WeightedTask objects
- Matches task labels against rules to assign weights
- Filters out tasks without matching labels
- Located in `rescheduler.py:30-49`

### Testing Structure

Tests use a fake API pattern:
- `tests/helpers/fake_api.py` - FakeTodoistAPI implements TodoistAPIProtocol
- `tests/helpers/data_generators.py` - Factory functions for test data
- `tests/conftest.py` - Shared fixtures (loop, params, logging setup)

The FakeTodoistAPI tracks update_task calls and provides `task_distribution()` to verify rescheduling behavior.

## Configuration

### Rules File Format (JSON)
```json
{
  "max_weight": 10,  // or per-day: {"sunday": 5, "monday": 10, ...}
  "rules": [
    {"filter": "@< 15 min", "weight": 2},
    {"filter": "@< 60 min", "weight": 4}
  ]
}
```

Rules use Todoist label syntax (filter starts with `@`). The rescheduler strips the `@` prefix when matching against task labels.

### Environment Variables
- `TODOIST_USER_TOKEN` - Todoist API token (can override with `--token`)
- `RETRY_ATTEMPTS` - Number of retry attempts for API calls (default: 3)

## Important Patterns

### Async/Await
The codebase is fully async:
- All API calls use `await`
- Multiple task updates are batched with `asyncio.gather()`
- Retry decorators work with async functions

### Dependency Injection
Uses Protocol types (not ABC) for interfaces:
- `TodoistAPIProtocol` allows easy test fakes
- Makes the CLI testable with `postpwn()` function that accepts an API instance

### Date/Time Handling
- Uses `zoneinfo.ZoneInfo` for timezone support (Python 3.9+)
- Preserves task time information when rescheduling
- Handles both date-only and datetime dues

## Known Limitations

From README TODO section:
- Timezone/DST edge cases need more test coverage
- No semantic release yet
- Cron validation could be improved
