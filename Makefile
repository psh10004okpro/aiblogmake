.PHONY: help setup install run test clean docker-up docker-down docker-logs migrate-up migrate-down migrate-current migrate-history

help:
	@echo "Blog Automation System - Available Commands"
	@echo ""
	@echo "  make setup             - Initial project setup"
	@echo "  make install           - Install dependencies"
	@echo "  make run               - Run FastAPI server locally"
	@echo "  make test              - Run tests"
	@echo "  make test-cov          - Run tests with coverage"
	@echo "  make lint              - Run linters"
	@echo "  make format            - Format code with black"
	@echo "  make migrate-up        - Apply database migrations"
	@echo "  make migrate-down      - Rollback last migration"
	@echo "  make migrate-current   - Show current migration"
	@echo "  make migrate-history   - Show migration history"
	@echo "  make migrate-auto      - Auto-generate migration from models"
	@echo "  make docker-up         - Start Docker services"
	@echo "  make docker-down       - Stop Docker services"
	@echo "  make docker-logs       - View Docker logs"
	@echo "  make docker-migrate    - Run migrations in Docker"
	@echo "  make clean             - Clean temporary files"

setup:
	@bash scripts/setup.sh

install:
	pip install -r requirements.txt
	playwright install chromium

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term

lint:
	flake8 app tests
	mypy app

format:
	black app tests
	isort app tests

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-build:
	docker-compose build

docker-migrate:
	docker-compose exec api alembic upgrade head

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
