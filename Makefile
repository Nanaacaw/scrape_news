help:
	@echo "Targets:"
	@echo "  install        Install python deps"
	@echo "  install-api    Install API deps only"
	@echo "  install-worker Install worker deps only"
	@echo "  init           Initialize database"
	@echo "  scrape         Scrape from all sources"
	@echo "  analyze        Run sentiment analysis"
	@echo "  api            Run FastAPI (dev)"
	@echo "  api-dev        Run FastAPI (reload)"
	@echo "  api-prod       Run FastAPI (prod)"
	@echo "  scheduler      Run scheduler worker"
	@echo "  test           Run tests"
	@echo "  docker-up      Start Docker Compose"
	@echo "  docker-down    Stop Docker Compose"

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

install:
	pip install -r requirements.txt

install-api:
	pip install -r requirements/api.txt

install-worker:
	pip install -r requirements/worker.txt

init:
	python main.py init

scrape:
	python main.py scrape --source all --limit 50

scrape-cnbc:
	python main.py scrape --source cnbc --limit 30

scrape-bloomberg:
	python main.py scrape --source bloomberg --limit 30

analyze:
	python main.py analyze

search:
ifndef TICKER
	@echo "Usage: make search TICKER=BBRI"
	@exit 1
endif
	python main.py search --ticker $(TICKER) --limit 10

stats:
	python main.py stats

api:
	python -m src.api.main

api-dev:
	uvicorn src.api.main:app --reload --port 8000

api-prod:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

scheduler:
	python -m src.scraper.scheduler

test:
	pytest tests/ -v

clean:
	@echo Cleaning cache and temporary files...
	@if exist __pycache__ rd /s /q __pycache__
	@if exist .pytest_cache rd /s /q .pytest_cache
	@for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
	@for /d /r %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d"
	@echo Done!

# Quick combined workflows
quick-start: init scrape api

full-pipeline: install init scrape analyze stats
