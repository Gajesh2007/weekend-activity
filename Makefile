.PHONY: install test lint format clean docs help

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package and development dependencies
	poetry install --with dev

test:  ## Run tests with pytest
	poetry run pytest tests/ --cov=weekend_activity --cov-report=term-missing

lint:  ## Run linting checks
	poetry run flake8 weekend_activity tests
	poetry run black --check weekend_activity tests

format:  ## Format code with black
	poetry run black weekend_activity tests

clean:  ## Clean up build artifacts
	rm -rf build/ dist/ *.egg-info .coverage .pytest_cache __pycache__ .tox
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docs:  ## Generate documentation
	cd docs && poetry run sphinx-build -b html . _build/html

setup-dev:  ## Set up development environment
	cp example.config.yaml config.yaml
	poetry install --with dev

run:  ## Run the weekend activity tracker
	poetry run weekend-activity report
