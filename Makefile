.PHONY: help install dev test deploy clean

PI_HOST ?= 192.168.1.100
PI_USER ?= pi

help:
	@echo "Smart Camera - Development & Deployment"
	@echo ""
	@echo "LOCAL DEVELOPMENT:"
	@echo "  make install    - Setup venv and install dependencies locally"
	@echo "  make dev        - Run backend locally (needs camera or will fallback to OpenCV)"
	@echo "  make test       - Run test suite"
	@echo "  make clean      - Remove venv and __pycache__"
	@echo ""
	@echo "DEPLOYMENT TO RASPBERRY PI:"
	@echo "  make deploy PI_HOST=<ip> PI_USER=<user>"
	@echo "    Example: make deploy PI_HOST=192.168.1.100 PI_USER=pi"
	@echo ""

install:
	@echo "Setting up Python environment..."
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip setuptools wheel
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✓ Environment ready. Activate with: source venv/bin/activate"

dev:
	@echo "Starting Smart Camera backend (localhost:5001)..."
	. venv/bin/activate && python3 run.py

test:
	@echo "Running test suite..."
	. venv/bin/activate && python3 test.py

deploy:
	@if [ -z "$(PI_HOST)" ]; then \
		echo "Usage: make deploy PI_HOST=<ip> [PI_USER=<user>]"; \
		exit 1; \
	fi
	@echo "Deploying to $(PI_USER)@$(PI_HOST)..."
	./deploy.sh $(PI_HOST) $(PI_USER)

clean:
	@echo "Cleaning up..."
	rm -rf venv __pycache__ .pytest_cache
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete
	@echo "✓ Cleaned"

requirements-update:
	@echo "Updating requirements.txt..."
	. venv/bin/activate && pip freeze > requirements.txt.new
	@echo "Review changes in requirements.txt.new, then move to requirements.txt"

lint:
	@echo "Linting Python code..."
	. venv/bin/activate && python3 -m flake8 backend/ --max-line-length=120 || true
	@echo "Note: Install flake8 with: pip install flake8"

