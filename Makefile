.PHONY: help setup install run test test-unit test-integration test-e2e test-cov test-fast test-slow test-watch clean docker-up docker-down docker-logs migrate-up migrate-down migrate-current migrate-history celery-worker celery-beat celery-all celery-stop celery-flower celery-logs celery-status docker-celery-worker docker-celery-beat docker-celery-logs docker-flower

help:
	@echo "Blog Automation System - Available Commands"
	@echo ""
	@echo "  make setup             - Initial project setup"
	@echo "  make install           - Install dependencies"
	@echo "  make run               - Run FastAPI server locally"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test              - Run all tests"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-integration  - Run integration tests"
	@echo "  make test-e2e          - Run end-to-end tests"
	@echo "  make test-service      - Run service layer tests"
	@echo "  make test-api          - Run API endpoint tests"
	@echo "  make test-cov          - Run tests with coverage report"
	@echo "  make test-fast         - Run fast tests (skip slow/external)"
	@echo "  make test-slow         - Run slow tests only"
	@echo "  make test-watch        - Run tests in watch mode"
	@echo "  make test-failed       - Re-run only failed tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              - Run linters"
	@echo "  make format            - Format code with black"
	@echo "  make type-check        - Run mypy type checking"
	@echo ""
	@echo "Database Migrations:"
	@echo "  make migrate-up        - Apply database migrations"
	@echo "  make migrate-down      - Rollback last migration"
	@echo "  make migrate-current   - Show current migration"
	@echo "  make migrate-history   - Show migration history"
	@echo "  make migrate-auto      - Auto-generate migration from models"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-up         - Start Docker services"
	@echo "  make docker-down       - Stop Docker services"
	@echo "  make docker-logs       - View Docker logs"
	@echo "  make docker-migrate    - Run migrations in Docker"
	@echo "  make docker-test       - Run tests in Docker"
	@echo ""
	@echo "Celery Commands:"
	@echo "  make celery-worker     - Start Celery worker locally"
	@echo "  make celery-beat       - Start Celery Beat scheduler locally"
	@echo "  make celery-all        - Start both worker and beat"
	@echo "  make celery-stop       - Stop all Celery services"
	@echo "  make celery-flower     - Start Flower (Celery monitoring)"
	@echo "  make celery-logs       - View Celery logs"
	@echo ""
	@echo "  make clean             - Clean temporary files"

setup:
	@bash scripts/setup.sh

install:
	pip install -r requirements.txt
	playwright install chromium

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ==================== 테스트 명령어 ====================

test:
	@echo "🧪 Running all tests..."
	pytest

test-unit:
	@echo "🧪 Running unit tests..."
	pytest -m unit -v

test-integration:
	@echo "🧪 Running integration tests..."
	pytest -m integration -v

test-e2e:
	@echo "🧪 Running end-to-end tests..."
	pytest -m e2e -v

test-service:
	@echo "🧪 Running service layer tests..."
	pytest -m service -v

test-api:
	@echo "🧪 Running API endpoint tests..."
	pytest -m api -v

test-fast:
	@echo "⚡ Running fast tests (skip slow/external)..."
	pytest -m "not slow and not external" -v

test-slow:
	@echo "🐌 Running slow tests..."
	pytest -m slow -v

test-cov:
	@echo "📊 Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term --cov-report=xml

test-cov-report:
	@echo "📊 Opening coverage report..."
	@python -m webbrowser -t htmlcov/index.html || open htmlcov/index.html || xdg-open htmlcov/index.html

test-watch:
	@echo "👀 Running tests in watch mode..."
	pytest-watch

test-failed:
	@echo "🔄 Re-running failed tests..."
	pytest --lf -v

test-verbose:
	@echo "🔍 Running tests with verbose output..."
	pytest -vvs

test-parallel:
	@echo "⚡ Running tests in parallel..."
	pytest -n auto

# ==================== 코드 품질 ====================

lint:
	@echo "🔍 Running linters..."
	flake8 app tests
	@echo "✅ Linting complete!"

type-check:
	@echo "🔍 Running type checks..."
	mypy app
	@echo "✅ Type checking complete!"

format:
	@echo "✨ Formatting code..."
	black app tests
	isort app tests
	@echo "✅ Formatting complete!"

format-check:
	@echo "🔍 Checking code format..."
	black --check app tests
	isort --check app tests

# ==================== Docker 명령어 ====================

docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d
	@echo "✅ Docker services started!"

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker-compose down
	@echo "✅ Docker services stopped!"

docker-logs:
	@echo "📋 Viewing Docker logs..."
	docker-compose logs -f

docker-build:
	@echo "🔨 Building Docker images..."
	docker-compose build
	@echo "✅ Docker images built!"

docker-migrate:
	@echo "🔄 Running migrations in Docker..."
	docker-compose exec api alembic upgrade head
	@echo "✅ Migrations complete!"

docker-test:
	@echo "🧪 Running tests in Docker..."
	docker-compose exec api pytest
	@echo "✅ Tests complete!"

docker-test-cov:
	@echo "📊 Running tests with coverage in Docker..."
	docker-compose exec api pytest --cov=app --cov-report=html --cov-report=term
	@echo "✅ Coverage report generated!"

docker-shell:
	@echo "🐚 Opening shell in Docker container..."
	docker-compose exec api /bin/bash

# Database Migration Commands
migrate-up:
	@bash scripts/migrate.sh upgrade

migrate-down:
	@bash scripts/migrate.sh downgrade 1

migrate-current:
	@bash scripts/migrate.sh current

migrate-history:
	@bash scripts/migrate.sh history

migrate-auto:
	@read -p "Migration message: " msg; \
	bash scripts/migrate.sh autogenerate -m "$$msg"

migrate-init:
	@bash scripts/migrate.sh init

# ==================== Celery 명령어 ====================

celery-worker:
	@echo "👷 Starting Celery Worker..."
	@bash scripts/start_celery_worker.sh

celery-beat:
	@echo "⏰ Starting Celery Beat..."
	@bash scripts/start_celery_beat.sh

celery-all:
	@echo "🚀 Starting all Celery services..."
	@bash scripts/start_celery_all.sh

celery-stop:
	@echo "🛑 Stopping all Celery services..."
	@bash scripts/stop_celery_all.sh

celery-flower:
	@echo "🌸 Starting Flower (Celery monitoring)..."
	@mkdir -p logs
	celery -A app.tasks.celery_tasks flower --port=5555

celery-logs:
	@echo "📋 Viewing Celery logs..."
	@tail -f logs/celery-*.log

celery-status:
	@echo "📊 Celery services status:"
	@ps aux | grep -E "(celery worker|celery beat|flower)" | grep -v grep || echo "No Celery services running"

# Docker Celery commands
docker-celery-worker:
	@echo "👷 Restarting Celery Worker in Docker..."
	docker-compose restart celery-worker

docker-celery-beat:
	@echo "⏰ Restarting Celery Beat in Docker..."
	docker-compose restart celery-beat

docker-celery-logs:
	@echo "📋 Viewing Celery logs in Docker..."
	docker-compose logs -f celery-worker celery-beat

docker-flower:
	@echo "🌸 Opening Flower dashboard..."
	@echo "Flower: http://localhost:5555"
	@python -m webbrowser http://localhost:5555 || open http://localhost:5555 || xdg-open http://localhost:5555

# ==================== Clean ====================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -f celery-worker.pid celery-beat.pid
	rm -f celerybeat-schedule.db
