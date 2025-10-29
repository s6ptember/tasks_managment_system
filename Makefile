# Makefile for Task Manager Project

.PHONY: help build up down restart logs shell migrate makemigrations collectstatic createsuperuser test clean ssl-setup pwa-icons

# Colors for output
BLUE=\033[0;34m
GREEN=\033[0;32m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Task Manager - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build

up: ## Start all containers
	@echo "$(BLUE)Starting containers...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Containers started!$(NC)"
	@echo "$(BLUE)Application available at: https://domen.com$(NC)"

down: ## Stop all containers
	@echo "$(BLUE)Stopping containers...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Containers stopped!$(NC)"

restart: down up ## Restart all containers

logs: ## View logs from all containers
	docker-compose logs -f

logs-web: ## View logs from web container
	docker-compose logs -f web

logs-nginx: ## View logs from nginx container
	docker-compose logs -f nginx

logs-db: ## View logs from database container
	docker-compose logs -f db

shell: ## Open shell in web container
	docker-compose exec web sh

shell-db: ## Open PostgreSQL shell
	docker-compose exec db psql -U postgres -d task_management

migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	docker-compose exec web python src/manage.py migrate
	@echo "$(GREEN)✓ Migrations completed!$(NC)"

makemigrations: ## Create new migrations
	@echo "$(BLUE)Creating migrations...$(NC)"
	docker-compose exec web python src/manage.py makemigrations
	@echo "$(GREEN)✓ Migrations created!$(NC)"

collectstatic: ## Collect static files
	@echo "$(BLUE)Collecting static files...$(NC)"
	docker-compose exec web python src/manage.py collectstatic --noinput
	@echo "$(GREEN)✓ Static files collected!$(NC)"

createsuperuser: ## Create Django superuser
	docker-compose exec web python src/manage.py createsuperuser

test: ## Run tests
	docker-compose exec web python src/manage.py test

clean: ## Remove all containers, volumes, and images
	@echo "$(RED)Warning: This will remove all containers, volumes, and images!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v --rmi all; \
		echo "$(GREEN)✓ Cleaned up!$(NC)"; \
	fi

ssl-setup: ## Setup SSL certificates
	@echo "$(BLUE)SSL Certificate Setup$(NC)"
	@bash scripts/setup_ssl.sh

pwa-icons: ## Generate PWA icons from source image
	@echo "$(BLUE)Generating PWA icons...$(NC)"
	@read -p "Enter path to source image: " IMAGE_PATH; \
	python scripts/generate_pwa_icons.py $$IMAGE_PATH
	@echo "$(GREEN)✓ PWA icons generated!$(NC)"

init: ## Initial setup (build, migrate, collectstatic, create superuser)
	@echo "$(BLUE)Initial project setup...$(NC)"
	@make build
	@make up
	@echo "Waiting for services to start..."
	@sleep 5
	@make migrate
	@make collectstatic
	@echo "$(GREEN)✓ Setup completed!$(NC)"
	@echo "$(BLUE)Create superuser:$(NC)"
	@make createsuperuser

backup-db: ## Backup database
	@echo "$(BLUE)Creating database backup...$(NC)"
	@mkdir -p backups
	docker-compose exec -T db pg_dump -U postgres task_management > backups/db_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Database backup created!$(NC)"

restore-db: ## Restore database from backup (use BACKUP=filename)
	@echo "$(BLUE)Restoring database...$(NC)"
	@if [ -z "$(BACKUP)" ]; then \
		echo "$(RED)Error: Please specify BACKUP=filename$(NC)"; \
		echo "Example: make restore-db BACKUP=backups/db_backup_20250127_123456.sql"; \
		exit 1; \
	fi
	docker-compose exec -T db psql -U postgres task_management < $(BACKUP)
	@echo "$(GREEN)✓ Database restored!$(NC)"

status: ## Show status of all containers
	@echo "$(BLUE)Container Status:$(NC)"
	@docker-compose ps

update: ## Pull latest changes and restart
	@echo "$(BLUE)Updating application...$(NC)"
	git pull
	@make build
	@make restart
	@make migrate
	@make collectstatic
	@echo "$(GREEN)✓ Update completed!$(NC)"

dev-setup: ## Setup for development (with hot reload)
	@echo "$(BLUE)Setting up development environment...$(NC)"
	cp .env.example .env
	@echo "$(GREEN)✓ .env file created. Please edit it with your settings.$(NC)"
	@echo "$(BLUE)Installing Python dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Setup completed!$(NC)"
	@echo "Run 'python src/manage.py runserver' to start development server"

# Default target
.DEFAULT_GOAL := help
