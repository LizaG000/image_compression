compose:
	docker compose -f deploy/docker-compose.yml up --build -d
	docker exec -it deploy-backend-1 alembic upgrade head

down:
	docker compose -f deploy/docker-compose.yml down

migrations_init:
	docker exec -it deploy-backend-1 alembic revision --autogenerate -m "init"

makemigrations:
	docker exec -it deploy-backend-1 alembic revision --autogenerate -m "$(MSG)"

migrate:
	docker exec -it deploy-backend-1 alembic upgrade head

downgrade:
	docker exec -it deploy-backend-1 alembic downgrade -1
