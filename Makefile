.DEFAULT_GOAL := help

ifeq ($(OS),Windows_NT)
  PYTHON_PATH := $(shell where python 2>NUL || where py 2>NUL)
else
  PYTHON_PATH := $(shell command -v python || command -v python3)
endif

PYTHON_NAME := $(notdir $(lastword $(PYTHON_PATH)))
PYTHON := $(basename $(PYTHON_NAME))

.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Default target: help"
	@echo ""
	@echo "Targets:"
	@echo " help             Show this message and exit"
	@echo " requirements     Generate requirements/*.txt files"
	@echo " format           Run the formatters for the python package"
	@echo " lint             Run the linters for the python package"
	@echo " forlint          Alias for 'format' and 'lint'"
	@echo " clean            Cleanup unneeded files"
	@echo " test             Run the tests for the python package"
	@echo " images           Build all container images."
	@echo " eva-image        Build eva container image."
	@echo " avatar-image     Build avatar container image."


.PHONY: requirements
requirements:
	$(PYTHON) scripts/requirements.py

.PHONY: format
format:
	black --config pyproject.toml eva tests scripts
	autoflake --in-place --remove-all-unused-imports --remove-unused-variables --recursive eva tests scripts
	ruff format --config pyproject.toml eva tests scripts

.PHONY: lint
lint:
	black --config pyproject.toml --check --diff eva tests scripts
	ruff check --config pyproject.toml eva tests scripts
	flake8 --config .flake8 eva tests scripts
	yamllint .
	mypy --config pyproject.toml eva tests scripts
	bandit -r -c pyproject.toml eva scripts
	pylint --rcfile=pyproject.toml eva tests scripts

.PHONY: forlint
forlint: format lint

.PHONY: clean
clean:
	$(PYTHON) scripts/clean.py

.PHONY: test
test:
	pip install -qq -r requirements/test.txt
	pytest -c pyproject.toml --cov=eva --cov-branch --cov-report=term-missing:skip-covered --cov-report=lcov:coverage/eva/lcov.info --cov-report=html:coverage/eva/html --cov-report=xml:coverage/eva/coverage.xml --junitxml=coverage/eva/xunit.xml tests

.PHONY: images
images:
	$(PYTHON) scripts/image.py

.PHONY: eva-image
eva-image:
	$(PYTHON) scripts/image.py --image-name thingenious/sermas-eva --service-name eva

.PHONY: eva_image
eva_image: eva-image

.PHONY: avatar-image
avatar-image:
	$(PYTHON) scripts/image.py --image-name thingenious/sermas-avatar --service-name avatar

.PHONY: avatar_image
avatar_image: avatar-image
