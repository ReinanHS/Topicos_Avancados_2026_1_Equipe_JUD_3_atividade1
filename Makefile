check:
	uv run ruff check
	uv run ruff format
	uv run complexipy src
install:
	uv sync
run:
	uv run reinan-cli
puml:
	uv run py2puml src src > docs/diagrama_classes.puml
