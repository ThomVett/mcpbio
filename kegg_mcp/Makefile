.PHONY: format install-dev help

help:
	@echo "Available commands:"
	@echo "  make format     Run ruff formatter on Python files"
	@echo "  make install-dev   Install development dependencies"

install-dev:
	uv pip install -e ".[dev]"

format:
	ruff format . 