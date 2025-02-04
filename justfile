@setup-dotenv:
  sh scripts/setup-dotenv.sh

run *args='':
    uv run that-what-must-be-done {{args}}

@lint:
  uv run ruff check
