#!/bin/bash

# Script to sort imports and format code using black for files in the src directory

FOLDERS=("src" "tests")

# https://stackoverflow.com/a/78156861/16668046
echo "-> running ruff sort ..."
uv run ruff check --select I --fix "${FOLDERS[@]}" # Sort imports using ruff

echo "-> running ruff format ..."
uv run ruff format "${FOLDERS[@]}" # Format code using ruff

echo "-> running mypy ..."
uv run mypy "${FOLDERS[@]}" --check-untyped-defs # Run mypy to check types

echo "-> running pyright ..."
uv run pyright "${FOLDERS[@]}"
