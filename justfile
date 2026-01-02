@setup-dotenv:
  sh scripts/setup-dotenv.sh

run *args='':
    uv run postpwn {{args}}

@typecheck:
  uv run basedpyright

@lint:
  uv run ruff check

@test:
  uv run pytest

@check-formatting:
  uv run ruff format --check

@format:
  uv run ruff format

@verify: check-formatting lint typecheck test
  echo "Format, lint, type, and test checks passed!"
  
