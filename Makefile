.PHONY: run-backend run-frontend test clean

run-backend:
	cd backend && python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

run-frontend:
	cd frontend && npm start

test:
	cd backend && python ../scripts/test_agents.py

test-backend:
	cd backend && python ../scripts/test_agents.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/node_modules frontend/build

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down
