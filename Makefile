# =============================================================================
# BESIKTNINGSAPP - MAKEFILE
# =============================================================================
# Common commands for development, testing, and deployment

.PHONY: help
help: ## Show this help message
	@echo "Besiktningsapp - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# SETUP & INSTALLATION
# =============================================================================

.PHONY: install
install: ## Install all dependencies (backend + mobile)
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing mobile dependencies..."
	cd mobile && npm install
	@echo "✓ Installation complete!"

.PHONY: install-dev
install-dev: ## Install development dependencies
	@echo "Installing backend dev dependencies..."
	cd backend && pip install -r requirements-dev.txt
	@echo "Installing mobile dev dependencies..."
	cd mobile && npm install --include=dev
	@echo "✓ Dev installation complete!"

.PHONY: setup
setup: ## Initial setup (create .env, init db)
	@echo "Setting up environment..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file"; fi
	@echo "Starting services..."
	$(MAKE) up
	@sleep 5
	@echo "Initializing database..."
	$(MAKE) db-init
	@echo "✓ Setup complete!"

# =============================================================================
# DOCKER COMPOSE
# =============================================================================

.PHONY: up
up: ## Start all services (development)
	docker-compose up -d

.PHONY: down
down: ## Stop all services
	docker-compose down

.PHONY: restart
restart: ## Restart all services
	docker-compose restart

.PHONY: logs
logs: ## Show logs from all services
	docker-compose logs -f

.PHONY: logs-backend
logs-backend: ## Show backend logs
	docker-compose logs -f backend

.PHONY: ps
ps: ## Show running containers
	docker-compose ps

.PHONY: build
build: ## Build all Docker images
	docker-compose build

.PHONY: clean
clean: ## Stop and remove all containers, networks, volumes
	docker-compose down -v --remove-orphans
	@echo "✓ Cleaned up!"

# =============================================================================
# PRODUCTION DOCKER COMPOSE
# =============================================================================

.PHONY: prod-up
prod-up: ## Start production environment
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

.PHONY: prod-down
prod-down: ## Stop production environment
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

.PHONY: prod-build
prod-build: ## Build production images
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

.PHONY: prod-logs
prod-logs: ## Show production logs
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# =============================================================================
# DATABASE
# =============================================================================

.PHONY: db-init
db-init: ## Initialize database with schema
	docker-compose exec backend flask db upgrade
	docker-compose exec backend python scripts/seed_data.py

.PHONY: db-migrate
db-migrate: ## Create new migration (use MSG="description")
	docker-compose exec backend flask db migrate -m "$(MSG)"

.PHONY: db-upgrade
db-upgrade: ## Apply migrations
	docker-compose exec backend flask db upgrade

.PHONY: db-downgrade
db-downgrade: ## Rollback last migration
	docker-compose exec backend flask db downgrade

.PHONY: db-shell
db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U besiktning -d besiktningsapp

.PHONY: db-backup
db-backup: ## Backup database
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U besiktning besiktningsapp > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✓ Database backed up to backups/"

.PHONY: db-restore
db-restore: ## Restore database (use FILE=backups/backup.sql)
	@if [ -z "$(FILE)" ]; then echo "Error: FILE not specified. Use: make db-restore FILE=backups/backup.sql"; exit 1; fi
	docker-compose exec -T postgres psql -U besiktning -d besiktningsapp < $(FILE)
	@echo "✓ Database restored from $(FILE)"

# =============================================================================
# BACKEND
# =============================================================================

.PHONY: backend-shell
backend-shell: ## Open backend container shell
	docker-compose exec backend /bin/bash

.PHONY: backend-test
backend-test: ## Run backend tests
	docker-compose exec backend pytest -v

.PHONY: backend-test-cov
backend-test-cov: ## Run backend tests with coverage
	docker-compose exec backend pytest --cov=app --cov-report=html --cov-report=term

.PHONY: backend-lint
backend-lint: ## Lint backend code
	docker-compose exec backend flake8 app tests
	docker-compose exec backend black --check app tests
	docker-compose exec backend mypy app

.PHONY: backend-format
backend-format: ## Format backend code
	docker-compose exec backend black app tests
	docker-compose exec backend isort app tests

.PHONY: backend-flask
backend-flask: ## Run Flask CLI command (use CMD="command")
	docker-compose exec backend flask $(CMD)

# =============================================================================
# MOBILE
# =============================================================================

.PHONY: mobile-start
mobile-start: ## Start React Native development server
	cd mobile && npm start

.PHONY: mobile-android
mobile-android: ## Run on Android emulator
	cd mobile && npm run android

.PHONY: mobile-ios
mobile-ios: ## Run on iOS simulator
	cd mobile && npm run ios

.PHONY: mobile-test
mobile-test: ## Run mobile tests
	cd mobile && npm test

.PHONY: mobile-lint
mobile-lint: ## Lint mobile code
	cd mobile && npm run lint

.PHONY: mobile-format
mobile-format: ## Format mobile code
	cd mobile && npm run format

# =============================================================================
# KUBERNETES
# =============================================================================

.PHONY: k8s-apply
k8s-apply: ## Apply all Kubernetes manifests
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secret.yaml
	kubectl apply -f k8s/postgres/
	kubectl apply -f k8s/minio/
	kubectl apply -f k8s/backend/
	@echo "✓ Kubernetes resources applied!"

.PHONY: k8s-delete
k8s-delete: ## Delete all Kubernetes resources
	kubectl delete -f k8s/backend/
	kubectl delete -f k8s/minio/
	kubectl delete -f k8s/postgres/
	kubectl delete -f k8s/secret.yaml
	kubectl delete -f k8s/configmap.yaml
	kubectl delete -f k8s/namespace.yaml
	@echo "✓ Kubernetes resources deleted!"

.PHONY: k8s-status
k8s-status: ## Show Kubernetes resources status
	kubectl get all -n besiktningsapp

.PHONY: k8s-logs
k8s-logs: ## Show Kubernetes logs (use POD=pod-name)
	kubectl logs -n besiktningsapp $(POD) -f

.PHONY: k8s-describe
k8s-describe: ## Describe Kubernetes resource (use RESOURCE=type/name)
	kubectl describe -n besiktningsapp $(RESOURCE)

# =============================================================================
# TESTING
# =============================================================================

.PHONY: test
test: ## Run all tests (backend + mobile)
	@echo "Running backend tests..."
	$(MAKE) backend-test
	@echo "Running mobile tests..."
	$(MAKE) mobile-test
	@echo "✓ All tests passed!"

.PHONY: test-unit
test-unit: ## Run unit tests only
	docker-compose exec backend pytest tests/unit -v

.PHONY: test-integration
test-integration: ## Run integration tests only
	docker-compose exec backend pytest tests/integration -v

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests
	docker-compose exec backend pytest tests/e2e -v

# =============================================================================
# CODE QUALITY
# =============================================================================

.PHONY: lint
lint: ## Lint all code (backend + mobile)
	$(MAKE) backend-lint
	$(MAKE) mobile-lint

.PHONY: format
format: ## Format all code (backend + mobile)
	$(MAKE) backend-format
	$(MAKE) mobile-format

.PHONY: security-check
security-check: ## Run security checks
	docker-compose exec backend safety check
	docker-compose exec backend bandit -r app
	cd mobile && npm audit

# =============================================================================
# MONITORING & DEBUGGING
# =============================================================================

.PHONY: health
health: ## Check service health
	@echo "Checking backend health..."
	@curl -f http://localhost:5000/health || echo "Backend unhealthy"
	@echo "\nChecking backend readiness..."
	@curl -f http://localhost:5000/ready || echo "Backend not ready"

.PHONY: redis-cli
redis-cli: ## Open Redis CLI
	docker-compose exec redis redis-cli

.PHONY: minio-console
minio-console: ## Open MinIO console
	@echo "MinIO Console: http://localhost:9001"
	@echo "Username: minioadmin"
	@echo "Password: minioadmin"

.PHONY: adminer
adminer: ## Open Adminer (database UI)
	@echo "Adminer: http://localhost:8080"
	@echo "System: PostgreSQL"
	@echo "Server: postgres"
	@echo "Username: besiktning"
	@echo "Password: besiktning"
	@echo "Database: besiktningsapp"

# =============================================================================
# UTILITIES
# =============================================================================

.PHONY: generate-secret
generate-secret: ## Generate a random secret key
	@python -c "import secrets; print(secrets.token_urlsafe(32))"

.PHONY: shell
shell: ## Open Python shell with app context
	docker-compose exec backend flask shell

.PHONY: routes
routes: ## Show all Flask routes
	docker-compose exec backend flask routes

.PHONY: version
version: ## Show version information
	@echo "Backend:"
	@docker-compose exec backend python --version
	@docker-compose exec backend flask --version
	@echo "\nMobile:"
	@cd mobile && node --version
	@cd mobile && npm --version

# =============================================================================
# KUBERNETES (minikube/kind)
# =============================================================================

K8S_OVERLAY ?= local

.PHONY: k8s-local-up
k8s-local-up: ## Starta minikube och deploya lokal overlay
	@echo "Starting minikube..."
	minikube start --driver=docker --memory=4096 --cpus=2
	@echo "Enabling nginx ingress..."
	minikube addons enable ingress
	@echo "Creating secrets from example (if not already done)..."
	@if [ ! -f k8s/overlays/local/secrets.yaml ]; then \
		cp k8s/overlays/local/secrets.yaml.example k8s/overlays/local/secrets.yaml; \
		echo "⚠  Redigera k8s/overlays/local/secrets.yaml med riktiga värden!"; \
	fi
	@echo "Applying k8s manifests..."
	kubectl apply -k k8s/overlays/local/
	@echo "Waiting for rollout..."
	kubectl rollout status deployment/backend -n besiktningsapp --timeout=120s
	@echo "✓ Local k8s deployment done!"
	@echo "Add to /etc/hosts:  $$(minikube ip)  besiktningsapp.local minio.local"

.PHONY: k8s-local-down
k8s-local-down: ## Ta bort lokal k8s-deployment
	kubectl delete -k k8s/overlays/local/ --ignore-not-found
	@echo "✓ Local k8s resources removed"

.PHONY: k8s-status
k8s-status: ## Visa status för alla k8s-resurser
	@echo "=== Pods ==="
	kubectl get pods -n besiktningsapp
	@echo "\n=== Services ==="
	kubectl get services -n besiktningsapp
	@echo "\n=== Ingress ==="
	kubectl get ingress -n besiktningsapp
	@echo "\n=== PVCs ==="
	kubectl get pvc -n besiktningsapp

.PHONY: k8s-logs
k8s-logs: ## Visa backend-loggar i k8s
	kubectl logs -n besiktningsapp -l app=backend --tail=100 -f

.PHONY: k8s-shell
k8s-shell: ## Öppna shell i backend-pod
	kubectl exec -n besiktningsapp -it \
		$$(kubectl get pod -n besiktningsapp -l app=backend -o jsonpath='{.items[0].metadata.name}') \
		-- /bin/bash

.PHONY: k8s-apply
k8s-apply: ## Applicera overlay (K8S_OVERLAY=local|production)
	kubectl apply -k k8s/overlays/$(K8S_OVERLAY)/ --server-side

.PHONY: k8s-diff
k8s-diff: ## Visa diff mot befintlig k8s-konfiguration
	kubectl diff -k k8s/overlays/$(K8S_OVERLAY)/ || true

.PHONY: k8s-db-migrate
k8s-db-migrate: ## Kör Alembic-migrationer i k8s
	kubectl exec -n besiktningsapp -it \
		$$(kubectl get pod -n besiktningsapp -l app=backend -o jsonpath='{.items[0].metadata.name}') \
		-- flask db upgrade

# =============================================================================
# DEPLOYMENT (scripts)
# =============================================================================

.PHONY: deploy-dev
deploy-dev: ## Deploy to development environment
	@echo "Deploying to development..."
	./scripts/deploy-dev.sh

.PHONY: deploy-staging
deploy-staging: ## Deploy to staging environment
	@echo "Deploying to staging..."
	./scripts/deploy-staging.sh

.PHONY: deploy-prod
deploy-prod: ## Deploy to production environment
	@echo "Deploying to production..."
	./scripts/deploy-prod.sh

# =============================================================================
# DOCUMENTATION
# =============================================================================

.PHONY: docs
docs: ## Generate API documentation
	docker-compose exec backend python scripts/generate_openapi.py > docs/openapi.yaml
	@echo "✓ API documentation generated in docs/openapi.yaml"

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	cd docs && python -m http.server 8000

# =============================================================================
# DEFAULT
# =============================================================================

.DEFAULT_GOAL := help
