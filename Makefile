.PHONY: help install dev build test deploy deploy-backend deploy-frontend clean audit-7d

help:
	@echo "BetBudAI Build Commands"
	@echo "======================="
	@echo "make install      - Install all dependencies"
	@echo "make dev          - Run local development environment"
	@echo "make test         - Run test suite"
	@echo "make build        - Build frontend bundle"
	@echo "make deploy       - Deploy to AWS (backend + frontend)"
	@echo "make deploy-backend - Deploy backend Lambdas only"
	@echo "make deploy-frontend - Deploy frontend to Amplify"
	@echo "make audit-7d     - Run fresh 7-day audit vs baseline"
	@echo "make clean        - Clean build artifacts"
	@echo "make lint         - Run code quality checks"
	@echo "make docker-up    - Start Docker containers"
	@echo "make docker-down  - Stop Docker containers"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ All dependencies installed"

dev:
	@echo "Starting development environment..."
	docker-compose up

test:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v --cov=.
	@echo "Running frontend tests..."
	cd frontend && npm test -- --coverage --watchAll=false

lint:
	@echo "Running code quality checks..."
	cd backend && black . --check && flake8 . && mypy .
	cd frontend && npm run lint

build:
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "✓ Frontend built to frontend/build/"

deploy: deploy-backend deploy-frontend
	@echo "✓ Deployment complete!"

deploy-backend:
	@echo "Deploying backend Lambdas..."
	cd backend/pipeline && python deploy.py
	@echo "✓ Backend deployed"

deploy-frontend:
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo "Deploying frontend to Amplify..."
	cd frontend && amplify publish --yes
	@echo "✓ Frontend deployed"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf frontend/build
	rm -rf backend/.pytest_cache
	rm -rf backend/.coverage
	rm -rf backend/__pycache__
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✓ Cleaned"

docker-up:
	docker-compose up -d
	@echo "✓ Docker containers started"

docker-down:
	docker-compose down
	@echo "✓ Docker containers stopped"

logs:
	docker-compose logs -f backend

logs-frontend:
	cd frontend && npm start

# Local development targets
backend-run:
	cd backend && flask run

frontend-run:
	cd frontend && npm start

# Production-like build
build-prod:
	@echo "Building production bundle..."
	cd frontend && npm run build
	@echo "✓ Production build ready in frontend/build/"

# Format code
format:
	@echo "Formatting code..."
	cd backend && black .
	cd frontend && npm run format

# Check dependencies for vulnerabilities
audit:
	@echo "Auditing dependencies..."
	cd backend && pip-audit
	cd frontend && npm audit

audit-7d:
	@echo "Running fresh 7-day race audit and baseline comparison..."
	python scripts/audit_last7_compare.py
