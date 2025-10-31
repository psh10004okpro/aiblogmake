#!/bin/bash

# Database Migration Helper Script
# 데이터베이스 마이그레이션 헬퍼 스크립트

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    print_error "Alembic is not installed. Please run: pip install alembic"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    print_info "Loaded environment variables from .env"
fi

# Help message
show_help() {
    cat << EOF
📊 Database Migration Helper

Usage: ./scripts/migrate.sh [COMMAND] [OPTIONS]

Commands:
    upgrade             최신 버전으로 업그레이드
    downgrade [N]       N 단계 다운그레이드 (기본: 1)
    current             현재 데이터베이스 버전 확인
    history             마이그레이션 히스토리
    revision            새 마이그레이션 생성 (수동)
    autogenerate        새 마이그레이션 자동 생성
    heads               적용되지 않은 마이그레이션
    init                초기 마이그레이션 적용
    reset               모든 마이그레이션 되돌리기 (주의!)
    backup              데이터베이스 백업
    help                이 도움말 표시

Examples:
    ./scripts/migrate.sh upgrade
    ./scripts/migrate.sh downgrade 1
    ./scripts/migrate.sh autogenerate -m "add user table"
    ./scripts/migrate.sh backup

EOF
}

# Backup database
backup_db() {
    print_info "Creating database backup..."

    # Extract database info from DATABASE_URL
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    DB_URL=${DATABASE_URL:-postgresql+asyncpg://user:password@localhost:5432/blog_automation}

    # Parse URL (simplified)
    DBNAME=$(echo $DB_URL | grep -oP '(?<=/)[^/]+$')
    BACKUP_FILE="backups/backup_${DBNAME}_$(date +%Y%m%d_%H%M%S).sql"

    mkdir -p backups

    print_info "Backing up database: $DBNAME"
    print_info "Backup file: $BACKUP_FILE"

    # Note: This assumes pg_dump is available and configured
    # Adjust credentials as needed
    # pg_dump $DBNAME > $BACKUP_FILE

    print_warning "Database backup requires pg_dump to be configured"
    print_warning "Please run manually: pg_dump $DBNAME > $BACKUP_FILE"
}

# Main command handling
case "${1:-help}" in
    upgrade)
        print_info "Upgrading database to latest version..."
        alembic upgrade head
        print_success "Database upgraded successfully!"
        ;;

    downgrade)
        STEPS=${2:-1}
        print_warning "Downgrading database by $STEPS step(s)..."
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            alembic downgrade -$STEPS
            print_success "Database downgraded successfully!"
        else
            print_info "Downgrade cancelled"
        fi
        ;;

    current)
        print_info "Current database version:"
        alembic current
        ;;

    history)
        print_info "Migration history:"
        alembic history
        ;;

    heads)
        print_info "Checking for pending migrations..."
        alembic heads
        ;;

    revision)
        shift
        print_info "Creating new migration (manual)..."
        alembic revision "$@"
        print_success "Migration created! Please edit the generated file."
        ;;

    autogenerate)
        shift
        print_info "Auto-generating migration from model changes..."
        alembic revision --autogenerate "$@"
        print_success "Migration auto-generated!"
        print_warning "Please review the generated migration before applying!"
        ;;

    init)
        print_info "Initializing database with initial migration..."
        alembic upgrade head
        print_success "Database initialized successfully!"
        ;;

    reset)
        print_error "⚠️  WARNING: This will destroy all data! ⚠️"
        read -p "Type 'RESET' to confirm: " -r
        echo
        if [[ $REPLY == "RESET" ]]; then
            print_info "Resetting database..."
            alembic downgrade base
            alembic upgrade head
            print_success "Database reset complete!"
        else
            print_info "Reset cancelled"
        fi
        ;;

    backup)
        backup_db
        ;;

    help|--help|-h)
        show_help
        ;;

    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
