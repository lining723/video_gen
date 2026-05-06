.PHONY: backend frontend test docker-up docker-down

backend:
	python3 -m backend.src.api.app

frontend:
	cd frontend && node server.js

test:
	python3 -m unittest discover -s backend/tests -v

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v
