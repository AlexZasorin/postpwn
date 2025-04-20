@setup-dotenv:
  sh scripts/setup-dotenv.sh

run *args='':
    uv run postpwn {{args}}

@lint:
  uv run ruff check

@test:
  uv run pytest

@check-formatting:
  uv run ruff format --check

@format:
  uv run ruff format

@verify: check-formatting lint test
  echo "Format, lint, and test checks passed!"
  
