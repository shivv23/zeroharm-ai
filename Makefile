.PHONY: run-backend run-frontend test clean

run-backend:
	cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

run-frontend:
	cd frontend && npm start

test:
	cd backend && python -m pytest tests/ -v

test-backend:
	cd backend && python -m pytest tests/ -v

test-legacy:
	cd backend && python ../scripts/test_agents.py

clean:
	@echo "Cleaning Python cache..."
	@if command -v find >/dev/null 2>&1; then \
		find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true; \
		find . -type f -name "*.pyc" -delete 2>/dev/null || true; \
	else \
		python -c "import os, shutil; [shutil.rmtree(p) for p in [os.path.join(r, d) for r, ds, _ in os.walk('.') for d in ds if d == '__pycache__']]" 2>/dev/null || true; \
		Remove-Item -Recurse -Force __pycache__ -ErrorAction SilentlyContinue 2>/dev/null || true; \
	fi
	rm -rf frontend/node_modules frontend/build

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
