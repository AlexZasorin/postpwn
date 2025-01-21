set shell := ["zsh", "-cu"]

@setup-dotenv:
  sh scripts/setup-dotenv.sh

@run:
  uv run that-what-must-be-done

@lint:
  uv run ruff check
