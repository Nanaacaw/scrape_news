# Docker Split + Cleanup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Pisahkan Docker setup per komponen (API vs scheduler/worker) dan rapikan codebase supaya `scraper + FastAPI + database` bisa jalan konsisten, gampang di-deploy, dan minim “dead code”.

**Architecture:** Tetap 1 codebase Python, tapi build 2 image: `api` (FastAPI + DB access) dan `worker` (scraper + pipeline + scheduler + sentiment). DB dijalankan terpisah (Postgres di Docker Compose). Scheduler *tidak* di-embed di API untuk menghindari duplicate job saat API run multi-worker.

**Tech Stack:** Python 3.10, FastAPI, SQLAlchemy, APScheduler, Postgres (Docker), pytest

---

## Current Findings (Baseline)

1. **Scraper & pipeline ada dan cukup lengkap** (`src/scraper/*`, `src/pipeline/data_pipeline.py`, `src/sentiment/analyzer.py`, `src/database/*`).
2. **FastAPI ada, tapi kemungkinan besar belum bisa jalan** karena route modules import `src.api.models.schemas` yang **tidak ada** di repo (`src/api/routes/*.py` mengacu ke modul ini).
3. **Docker saat ini “monolith”**: satu `Dockerfile` install semua dependency (termasuk `torch`, `transformers`, `playwright + chromium`) untuk semua service. Padahal API tidak butuh ML stack.
4. **`docker-compose.yml` meng-enable scheduler di dalam API** via `RUN_SCHEDULER=true` (lihat `src/api/main.py:42-49`). Ini riskan kalau pakai `uvicorn --workers > 1` → job bisa dobel.
5. **Ada dead/outdated scripts**:
   - `run_dashboard.py` mengacu ke `src/dashboard/app.py` yang tidak ada.
   - `check_db.py` mengimport `Sentiment` yang tidak ada di `src/database/models.py`.
6. **Dokumentasi belum konsisten**: README bilang SQLite, Compose pakai Postgres, ada referensi dashboard yang “REMOVED” tapi masih ada runner script.
7. **Tests belum ada** (Makefile menunjuk `tests/` tapi folder tidak ada).
8. **IDX tickers CSV tidak ada di repo** (`data/idx_stonks.csv` di-ignore via `.gitignore`). Akibatnya ticker extraction biasanya kosong (graceful, tapi fitur “952 saham” tidak jalan).

---

### Task 1: Buat test harness minimal (biar TDD bisa jalan)

**Files:**
- Create: `tests/test_api_imports.py`

**Step 1: Write the failing test**

```python
def test_fastapi_app_imports():
    from src.api.main import app  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL karena `src.api.models.schemas` belum ada.

**Step 3: Implement minimal test scaffolding**

Tidak perlu scaffolding tambahan dulu; cukup pastikan pytest bisa discover.

**Step 4: Run test again**

Run: `pytest -q`
Expected: masih FAIL sampai Task 2 selesai.

**Step 5: Commit**

Run:
```bash
git add tests/test_api_imports.py
git commit -m "test: add api import smoke test"
```

---

### Task 2: Perbaiki FastAPI dengan menambahkan Pydantic schemas yang hilang

**Files:**
- Create: `src/api/models/__init__.py`
- Create: `src/api/models/schemas.py`

**Step 1: Write the failing test**

Tambahkan assertion untuk memastikan schemas importable:

```python
def test_api_schemas_importable():
    from src.api.models.schemas import ArticleResponse  # noqa: F401
```

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL `ModuleNotFoundError: src.api.models`.

**Step 3: Write minimal implementation**

Create `src/api/models/__init__.py` (empty).

Create `src/api/models/schemas.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    url: str
    source: str
    category: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    scraped_date: Optional[datetime] = None

    tickers: List[str] = []
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    confidence: Optional[float] = None
    analyzed_date: Optional[datetime] = None


class ArticleListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    articles: List[ArticleResponse]


class SearchResponse(BaseModel):
    query: str
    total: int
    articles: List[ArticleResponse]


class SentimentTrendPoint(BaseModel):
    date: str
    avg_sentiment: float
    article_count: int
    positive: int
    neutral: int
    negative: int


class SentimentTrendResponse(BaseModel):
    ticker: str
    period_days: int
    data: List[SentimentTrendPoint]


class TickerComparison(BaseModel):
    ticker: str
    name: Optional[str] = None
    avg_sentiment: float
    article_count: int
    positive_ratio: float


class SentimentCompareResponse(BaseModel):
    period_days: int
    comparison: List[TickerComparison]


class SentimentSummary(BaseModel):
    ticker: Optional[str] = None
    period_days: int
    total_articles: int
    sentiment_distribution: Dict[str, int]
    avg_sentiment_score: float
    top_positive: List[ArticleResponse]
    top_negative: List[ArticleResponse]


class TopTicker(BaseModel):
    ticker: str
    name: Optional[str] = None
    article_count: int
    avg_sentiment: float


class TopTickersResponse(BaseModel):
    top_tickers: List[TopTicker]


class StatsOverview(BaseModel):
    total_articles: int
    total_tickers: int
    sources: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    last_updated: datetime


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
```

**Step 4: Run test to verify it passes**

Run: `pytest -q`
Expected: PASS untuk tests yang hanya import (route tests belum).

**Step 5: Commit**

```bash
git add src/api/models/__init__.py src/api/models/schemas.py tests/test_api_imports.py
git commit -m "fix(api): add missing pydantic response schemas"
```

---

### Task 3: Rapikan route validation (FastAPI + Pydantic v2)

**Files:**
- Modify: `src/api/routes/articles.py:13`
- Modify: `src/api/routes/search.py:11`

**Step 1: Write the failing test**

Tambahkan test yang memastikan `Query(..., pattern=...)` dipakai (bukan `regex`) bila diperlukan oleh versi FastAPI/Pydantic yang dipakai.

Jika ternyata `regex=` masih valid di FastAPI versi project, skip perubahan ini.

**Step 2: Run test to verify it fails**

Run: `pytest -q`
Expected: FAIL hanya jika `regex=` sudah tidak didukung.

**Step 3: Implement minimal change**

Ganti:
- `Query(..., regex="...")` → `Query(..., pattern="...")`

Target:
- `src/api/routes/articles.py:18-19`
- `src/api/routes/search.py:15`

**Step 4: Run tests**

Run: `pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/api/routes/articles.py src/api/routes/search.py
git commit -m "chore(api): align query validation with pydantic v2"
```

---

### Task 4: Hapus / betulkan dead scripts (dashboard + check_db)

**Files:**
- Delete: `run_dashboard.py` (atau implement dashboard beneran)
- Modify: `check_db.py:1` (atau delete jika redundant)
- Modify: `README.md:200` (update doc supaya konsisten)

**Step 1: Write the failing test**

Tambahkan test sederhana yang memastikan script yang tersisa bisa dieksekusi/import tanpa error:

```python
def test_check_db_imports():
    import check_db  # noqa: F401
```

**Step 2: Run test**

Run: `pytest -q`
Expected: FAIL karena `Sentiment` tidak ada.

**Step 3: Implement minimal fix**

Opsi A (recommended): **hapus `check_db.py`** dan ganti dengan `python main.py stats` sebagai checker resmi.

Opsi B: perbaiki `check_db.py` supaya import `TickerSentiment` (atau hapus import yang salah).

Untuk `run_dashboard.py`, karena `src/dashboard/app.py` tidak ada dan README menyebut “REMOVED”, paling bersih adalah delete file + hapus bagian troubleshooting dashboard di README.

**Step 4: Run tests**

Run: `pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add README.md
git rm -f run_dashboard.py
git rm -f check_db.py  # jika pilih opsi A
git commit -m "chore: remove dead dashboard/db checker scripts"
```

---

### Task 5: Pisahkan scheduler dari API (hindari duplicate job saat multi-worker)

**Files:**
- Modify: `src/api/main.py:42`
- Modify: `docker-compose.yml:2`

**Step 1: Write failing test**

Add test untuk memastikan API tidak memulai scheduler saat import/startup (scheduler harus jalan di service terpisah).

**Step 2: Run**

Run: `pytest -q`
Expected: FAIL sampai startup hook dihapus/diubah.

**Step 3: Implement minimal change**

Di `src/api/main.py`, hapus `@app.on_event("startup")` block (line 42-49) atau ubah jadi hanya `init_database()` saja.

**Step 4: Run tests**

Run: `pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/api/main.py
git commit -m "refactor(api): stop embedding scheduler in api process"
```

---

### Task 6: Rapikan entrypoint scheduler agar tidak perlu sys.path hack

**Files:**
- Modify: `src/scraper/scheduler.py:1`
- Modify: `Makefile:35`

**Step 1: Write failing test**

Test import:
```python
def test_scheduler_module_imports():
    from src.scraper.scheduler import run_scheduler  # noqa: F401
```

**Step 2: Run**

Run: `pytest -q`
Expected: PASS/FAIL tergantung apakah sys.path hack mengganggu (biasanya PASS tapi ini cleanup).

**Step 3: Implement minimal change**

- Hapus block sys.path injection (`src/scraper/scheduler.py:1-6`).
- Ubah Makefile target `scheduler` jadi:
  - `python -m src.scraper.scheduler`

**Step 4: Run tests**

Run: `pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/scraper/scheduler.py Makefile
git commit -m "chore: run scheduler as module; remove sys.path hack"
```

---

### Task 7: Split Docker artifacts (Dockerfiles + entrypoints) per service

**Files:**
- Create: `docker/api.Dockerfile`
- Create: `docker/worker.Dockerfile`
- Create: `docker/entrypoint-api.sh`
- Create: `docker/entrypoint-worker.sh`
- Modify: `docker-compose.yml:1`
- Modify: `.dockerignore:1`

**Step 1: Write failing test**

Tambahkan `tests/test_docker_files_exist.py`:
```python
from pathlib import Path

def test_docker_artifacts_present():
    assert Path("docker/api.Dockerfile").exists()
    assert Path("docker/worker.Dockerfile").exists()
```

**Step 2: Run**

Run: `pytest -q`
Expected: FAIL (file belum ada).

**Step 3: Implement minimal Docker split**

`docker/api.Dockerfile` (API image ringan):
```dockerfile
FROM python:3.10-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker/entrypoint-api.sh
EXPOSE 8000
ENTRYPOINT ["docker/entrypoint-api.sh"]
```

`docker/worker.Dockerfile` (scraper+sentiment):
```dockerfile
FROM python:3.10-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker/entrypoint-worker.sh
ENTRYPOINT ["docker/entrypoint-worker.sh"]
```

`docker/entrypoint-api.sh`:
```bash
#!/usr/bin/env sh
set -eu
python -c "from src.database.connection import init_database; init_database()"
exec uvicorn src.api.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

`docker/entrypoint-worker.sh`:
```bash
#!/usr/bin/env sh
set -eu
python -c "from src.database.connection import init_database; init_database()"
exec python -m src.scraper.scheduler
```

Update `docker-compose.yml`:
- `api.build.dockerfile: docker/api.Dockerfile`
- `scheduler.build.dockerfile: docker/worker.Dockerfile`
- Hapus `RUN_SCHEDULER=true`

Update `.dockerignore` supaya tidak bawa `data/`, `logs/`, `models/` ke build context.

**Step 4: Run tests**

Run: `pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add docker/api.Dockerfile docker/worker.Dockerfile docker/entrypoint-api.sh docker/entrypoint-worker.sh docker-compose.yml .dockerignore tests/
git commit -m "feat(docker): split api and worker dockerfiles"
```

---

### Task 8: Optional tapi recommended — pisahkan requirements supaya image API lebih kecil

**Files:**
- Create: `requirements/api.txt`
- Create: `requirements/worker.txt`
- Modify: `docker/api.Dockerfile:1`
- Modify: `docker/worker.Dockerfile:1`
- Modify: `README.md:1`

**Step 1: Write failing test**

Test file exists:
```python
from pathlib import Path

def test_requirements_split_exists():
    assert Path("requirements/api.txt").exists()
    assert Path("requirements/worker.txt").exists()
```

**Step 2: Run**

Run: `pytest -q`
Expected: FAIL.

**Step 3: Implement**

`requirements/api.txt` minimal:
- `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `python-dotenv`, `loguru`, `pydantic`

`requirements/worker.txt`:
- scraper deps + scheduler + ML (`requests`, `bs4`, `lxml`, `apscheduler`, `transformers`, `torch`, `sentencepiece`, dll)

Update dockerfiles untuk install file yang sesuai.

**Step 4: Run tests**

Run: `pytest -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add requirements/ docker/api.Dockerfile docker/worker.Dockerfile README.md
git commit -m "chore: split api/worker requirements"
```

---

### Task 9: Update docs & deploy instructions (biar konsisten)

**Files:**
- Modify: `README.md:1`
- Modify: `API_USAGE.md:1`
- Modify: `.env.example:1`

**Step 1: Write failing test**

Tidak perlu test untuk docs; cukup manual review.

**Step 2: Implement docs updates**

Checklist:
- Jelaskan 2 mode DB: SQLite (default) vs Postgres (via `DATABASE_URL`).
- Update Docker usage:
  - `docker compose up -d db api scheduler`
  - scheduler bukan embedded di API.
- Hapus referensi dashboard jika memang tidak ada.
- Tambahkan catatan tentang `data/idx_stonks.csv`:
  - cara menyuplai file, atau buat script download di task terpisah.

**Step 3: Verify**

Run: `docker compose config` (pastikan compose valid)

**Step 4: Commit**

```bash
git add README.md API_USAGE.md .env.example
git commit -m "docs: align README with docker + api + db"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-02-05-docker-split-cleanup.md`. Two execution options:

1) **Subagent-Driven (this session)** - implement task-by-task, checkpoint tiap task
2) **Parallel Session (separate)** - eksekusi batch dengan checkpoint besar

Pilih yang mana, dan target deploy kamu di mana (VPS + Docker Compose, Railway, Fly.io, ECS, dll)?

