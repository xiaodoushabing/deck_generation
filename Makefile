SHELL := /bin/bash

# Install pre-commit and related tools
pc-install:
	pip install pre-commit pre-commit-hooks black interrogate isort pyproject-fmt nbstripout autoflake
	pre-commit install

# Run pre-commit on staged files
pc:
	pre-commit run

# Run pre-commit on all files
pc-all:
	pre-commit run --all-files

# Usage:
# make pc-hygiene			# runs on all files by default with verbose output
# make pc-hygiene F=""		# runs on added files only
# make pc-hygiene V=""		# runs on all files without verbose output

HYGIENE=check-repo-structure check-added-large-files nbstripout check-merge-conflict
VALIDATE=check-ast check-yaml check-json check-toml
FORMAT=isort black check-format pretty-format-json pyproject-fmt autoflake
DOCS=interrogate
SAFEGUARD=no-commit-to-branch

F ?= " -- all-files"
V = " -- v"

# run hygiene-related pre-commit hooks
pc-hygiene:
	@echo "Running hygiene checks ... "
	@for hook in $(HYGIENE); do \
		pre-commit run $$hook $(F) $(V); \
	done

# run validation-related pre-commit hooks
pc-validate:
	@echo "Running validation checks ... "
	@for hook in $(VALIDATE); do \
		pre-commit run $$hook $(F) $(V); \
	done

# run formatting-related pre-commit hooks
pc-format:
	@echo "Running format checks ... "
	@for hook in $(FORMAT); do \
	pre-commit run $$hook $(F) $(V); \
	done
# run documentation-related pre-commit hooks
pc-docs:
	@echo "Running documentation checks ... "
	@for hook in $(DOCS); do \
		pre-commit run $$hook $(F) $(V); \
	done

# run safeguard-related pre-commit hooks
pc-safeguard:
	@echo "Running safeguard checks ... "
	@for hook in $(SAFEGUARD); do \
		pre-commit run $$hook $(F) $(V); \
	done
# run interrogate
interrogate:
	interrogate -c pyproject.toml --exclude tests
# run isort
isort:
	isort .
# run black
black:
	black --config pyproject.toml .
# run autoflake
autoflake:
	autoflake --config pyproject.toml .
# clean caches and temporary files
clean:
	rm -rf _pycache_ .pytest_cache .mypy_cache

# run tests
test:
	python -m pytest \
		--cov=src \
		--cov-report term-missing \
		--durations=10 \
		tests
