install:
	pip install -r requirements.txt

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

api-prod:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4

scheduler:
	python src/scraper/scheduler.py

check-db:
	python check_db.py

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
