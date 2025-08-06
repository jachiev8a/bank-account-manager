# Makefile for Python virtual environment management
# Ensures Python 3.12 is used

.PHONY: venv clean install-deps install-dev test

# Python binary to use
PYTHON := python3.12

venv:
	@if [ ! -d ".venv" ]; then \
		command -v $(PYTHON) >/dev/null 2>&1 || { echo "Error: $(PYTHON) is required but not installed"; exit 1; }; \
		echo "Creating virtual environment with Python 3.12..."; \
		$(PYTHON) -m venv .venv; \
		echo "Virtual environment created at .venv/"; \
		echo "To activate, run: source .venv/bin/activate"; \
	else \
		echo "Virtual environment already exists at .venv/"; \
	fi

clean:
	@echo "Cleaning up virtual environment and generated files..."
	@rm -rf .venv
	@rm -rf __pycache__
	@rm -rf *.egg-info
	@rm -rf .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

install-deps: venv
	@echo "Installing dependencies..."
	@. .venv/bin/activate && pip install --upgrade pip
	@. .venv/bin/activate && pip install -r requirements.txt

test: venv
	@echo "Running tests..."
	@. .venv/bin/activate && pytest