# Voxpipe project management

set dotenv-load

# Default: show available recipes
default:
    @just --list

# Install dependencies
install:
    uv sync

# Build the package
build:
    uv build

# Run linter checks
lint:
    uv run ruff check src tests

# Format code
format:
    uv run ruff format src tests
    uv run ruff check --fix src tests

# Run type checking
typecheck:
    uv run mypy src

# Run tests
test *ARGS:
    uv run pytest {{ ARGS }}

# Run tests with coverage
test-cov:
    uv run pytest --cov=voxpipe --cov-report=term-missing --cov-report=html

# Check all (lint + typecheck + test)
check: lint typecheck test

# Clean build artifacts
clean:
    rm -rf dist/ build/ .pytest_cache/ .ruff_cache/ .mypy_cache/ .coverage htmlcov/
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Run the CLI
run *ARGS:
    uv run voxpipe {{ ARGS }}

# Show CLI help
help:
    uv run voxpipe --help
