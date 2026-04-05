check:
	uv run ruff check
	uv run ruff format
install:
	uv sync

run:
	uv run python main.py
