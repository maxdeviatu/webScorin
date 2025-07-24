.PHONY: dev lint format test install-deps install-playwright clean

# Development commands
dev:
	@echo "Starting development environment..."
	@echo "Starting API server..."
	poetry run uvicorn app.api:app --reload --host 0.0.0.0 --port 8000 & \
	echo "Starting Celery worker..." && \
	poetry run celery -A app.tasks worker --loglevel=info

# Start only the API server
api:
	poetry run uvicorn app.api:app --reload --host 0.0.0.0 --port 8000

# Start only the Celery worker
worker:
	poetry run celery -A app.tasks worker --loglevel=info

# Code quality
lint:
	poetry run ruff check .

format:
	poetry run black .

# Testing
test:
	poetry run pytest

# Install dependencies
install-deps:
	poetry install

# Install Playwright browsers
install-playwright:
	poetry run playwright install chromium

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf screenshots/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/

# Setup development environment
setup: install-deps install-playwright
	@echo "Development environment setup complete!"

# Start Redis (if not running)
redis:
	@echo "Starting Redis server..."
	redis-server --daemonize yes

# Stop Redis
redis-stop:
	redis-cli shutdown

# Show logs
logs:
	tail -f celery.log

# Help
help:
	@echo "Available commands:"
	@echo "  dev          - Start API and worker in development mode"
	@echo "  api          - Start only the API server"
	@echo "  worker       - Start only the Celery worker"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code with black"
	@echo "  test         - Run tests"
	@echo "  install-deps - Install Python dependencies"
	@echo "  install-playwright - Install Playwright browsers"
	@echo "  clean        - Clean up temporary files"
	@echo "  setup        - Complete development setup"
	@echo "  redis        - Start Redis server"
	@echo "  redis-stop   - Stop Redis server"
	@echo "  logs         - Show Celery logs"
	@echo "  help         - Show this help message" 