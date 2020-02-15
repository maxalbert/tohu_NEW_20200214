PYMODULE_NAME ?= tohu
PYTHON ?= poetry run python
PYTEST ?= poetry run pytest
PATH_TO_UNIT_TESTS ?= tests/
PATH_TO_NOTEBOOK_TESTS ?= notebooks/
PATH_TO_DOCS_NOTEBOOKS ?= docs/

all: test

test: remove-coverage-data-file regular-tests notebook-tests validate-docs-notebooks

remove-coverage-data-file:
	rm -f .coverage

# Run regular tests with pytest
regular-tests:
	$(PYTEST) --cov=$(PYMODULE_NAME) --cov-append $(PATH_TO_UNIT_TESTS)

# Validate jupyter notebooks using nbval.
#
# Note that for the time being we deactivate coverage reports for notebook tests due
# to a bug in nbval (see https://github.com/computationalmodelling/nbval/issues/116).
notebook-tests:
	$(PYTEST) --nbval --sanitize-with=nbval_sanitize_file.cfg --cov=$(PYMODULE_NAME) --cov-append $(PATH_TO_NOTEBOOK_TESTS)

validate-docs-notebooks:
	$(PYTEST) --nbval --sanitize-with=nbval_sanitize_file.cfg --cov=$(PYMODULE_NAME) --cov-append $(PATH_TO_DOCS_NOTEBOOKS)

# Build documentation
build-docs:
	poetry run mkdocs build

# Serve documentation locally (during development)
serve-docs:
	poetry run mkdocs serve

# Build distribution tarball and wheel
dist:
	mkdir -p dist/
	$(PYTHON) setup.py sdist bdist_wheel

.PHONY: all test regular-tests notebook-tests validate-docs-notebooks build-docs serve-docs dist
