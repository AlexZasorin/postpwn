@setup-dotenv:
  sh scripts/setup-dotenv.sh

run *args='':
    uv run postpwn {{args}}

@lint:
  uv run ruff check

@test:
  uv run pytest
