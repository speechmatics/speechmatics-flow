SOURCES := speechmatics_flow/ tests/ setup.py
VERSION ?= $(shell cat VERSION)

.PHONY: all
all: lint test

.PHONY: lint
lint:
	black --check --diff $(SOURCES)
	ruff $(SOURCES)

.PHONY: format
format:
	black $(SOURCES)

.PHONY: test
test: unittest

.PHONY: unittest
unittest:
	pytest -v tests

.PHONY: build
build:
	VERSION=$(VERSION) python setup.py sdist bdist_wheel
