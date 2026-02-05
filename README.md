# CNBC Market Scraping + Sentiment Analysis

> **News sentiment analysis system** yang mengintegrasikan web scraping dari CNBC Indonesia & Bloomberg Technoz dengan sentiment analysis menggunakan IndoBERT untuk analisis berita pasar.

## 📋 Features

- 🌐 **Web Scraping**: Otomatis scrape berita dari CNBC Indonesia & Bloomberg Technoz
- 🤖 **Sentiment Analysis**: Analisis sentiment menggunakan IndoBERT (Bahasa Indonesia)
- 📈 **Stock Ticker Database**: Integrasi lengkap dengan 952 saham Indonesia dari IDX
- ⏰ **Automated Scheduling**: Scraping otomatis dengan interval yang bisa dikustomisasi
- 💾 **Database**: SQLite (local dev) / Postgres (deploy)

## 🚀 Quick Start (Docker Compose)

### 1. Configuration

```bash
# Mac/Linux
cp .env.docker.example .env

# Windows (PowerShell)
# copy .env.docker.example .env
```

### 2. Start services

```bash
docker compose up -d --build
```

### 3. Run first scrape (optional)

```bash
docker compose exec scheduler python main.py scrape --source all --limit 10
```

### 4. Open API docs

Swagger UI: http://localhost:8000/docs

## 🧑‍💻 Local Development (without Docker)

```bash
cp .env.example .env

python -m venv venv
source venv/bin/activate
# pilih salah satu:
make install-api       # API only
make install-worker    # scraper + sentiment worker
# atau:
# make install         # full (superset)

python main.py init
python main.py scrape --source all --limit 10
make api-dev
```

## 📖 Usage Guide

### ⚡ Quick Start with Makefile

For convenience, use the provided Makefile:

```bash
# View all available commands
make help

# Common workflows
make install          # Install dependencies
make init            # Initialize database
make scrape          # Scrape from all sources
make api             # Start REST API server
make stats           # Show statistics

# Quick full setup
make full-pipeline   # install + init + scrape + analyze + stats
```

**Available Make Commands:**
- `make scrape-cnbc` / `make scrape-bloomberg` - Scrape specific source
- `make search TICKER=BBRI` - Search for ticker
- `make scheduler` - Run automated scheduler
- `make api-prod` - Run API in production mode
- `make clean` - Clean cache files

### CLI Commands

```bash
# Initialize database
python main.py init

# Scrape news articles from both sources
python main.py scrape --source all --limit 50

# Scrape from specific source
python main.py scrape --source cnbc --limit 30
python main.py scrape --source bloomberg --limit 30

# Run sentiment analysis on existing articles
python main.py analyze

# Search for specific stock ticker
python main.py search --ticker BBRI --limit 10

# Show database statistics
python main.py stats
```

### Scraping Options

| Source | URL | Description |
|--------|-----|-------------|
| `cnbc` | cnbcindonesia.com/market/indeks/5 | CNBC Indonesia Market index |
| `bloomberg` | bloombergtechnoz.com/indeks/market | Bloomberg Technoz Market news |
| `all` | Both sources | Comprehensive coverage |

### Automated Scheduling

Untuk menjalankan scraping otomatis sesuai interval:

```bash
python -m src.scraper.scheduler
```

Default: scrape setiap **1 jam** (bisa diatur di `.env`)

## 🌐 REST API

Project ini juga menyediakan RESTful API menggunakan FastAPI!

### Start API Server

```bash
# Development mode
python -m src.api.main

# Production mode
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

API Documentation: **http://localhost:8000/docs**

### Quick API Examples

```bash
# Get positive articles about BBRI
curl "http://localhost:8000/api/articles?ticker=BBRI&sentiment=positive&limit=10"

# Get sentiment trend for last 30 days
curl "http://localhost:8000/api/sentiment/trend?ticker=BBRI&days=30"

# Search articles
curl "http://localhost:8000/api/search?q=inflasi"

# Get statistics
curl "http://localhost:8000/api/stats/overview"
```

**Python example:**
```python
import requests

# Get articles
response = requests.get("http://localhost:8000/api/articles", params={
    "ticker": "BBRI", 
    "sentiment": "positive"
})
data = response.json()
print(f"Found {data['total']} articles")
```

📚 **Full API Documentation:** See [API_USAGE.md](API_USAGE.md) for detailed endpoints and examples


## 🏗️ Architecture

```
┌─────────────────┐
│ CNBC Indonesia  │
└────────┬────────┘
         │ scrape
         ▼
┌─────────────────┐
│  Web Scraper    │
│ (BeautifulSoup) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Pipeline  │
│  - Save to DB   │
│  - Sentiment    │
│  - Extract stocks
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Database       │
│ (SQLite/Postgres)│
│  - Articles     │
│  - TickerSentiments
└────┬──────┬─────┘
     │      │
     ▼      ▼
┌──────────────┐   ┌──────────────────┐
│  Sentiment   │   │     FastAPI      │
│   Analyzer   │   │   REST API       │
│  (IndoBERT)  │   │                  │
└──────────────┘   └──────────────────┘
```

## 📁 Project Structure

```
scrape_news/
├── main.py                      # CLI entry point
├── requirements.txt             # Dev dependencies (superset)
├── requirements/                # Split deps for Docker images
│   ├── api.txt
│   └── worker.txt
├── .env.example                 # Environment template
├── .gitignore
├── docker-compose.yml
├── docker/
│   ├── api.Dockerfile
│   ├── worker.Dockerfile
│   ├── entrypoint-api.sh
│   ├── entrypoint-worker.sh
│   └── wait_for_db.py
│
├── src/
│   ├── database/
│   │   ├── models.py           # SQLAlchemy models
│   │   └── connection.py       # Database connection
│   │
│   ├── scraper/
│   │   ├── cnbc_scraper.py     # CNBC web scraper
│   │   └── scheduler.py        # Automated scheduling
│   │
│   ├── sentiment/
│   │   └── analyzer.py         # IndoBERT sentiment analyzer
│   │
│   ├── pipeline/
│   │   └── data_pipeline.py    # Data processing pipeline
│   │
│   └── utils/
│       ├── config.py           # Configuration
│       ├── logger.py           # Logging
│       └── helpers.py          # Helper functions
│
├── tests/
│
├── data/                        # Optional data files (e.g., idx_stonks.csv)
├── logs/                        # Log files (auto-created)
└── models/                      # Cached models (auto-created)
```

## 📊 Stock Ticker Integration

### Complete IDX Database
- **952 Indonesian stocks** from Bursa Efek Indonesia (BEI/IDX)
- Automatic ticker extraction from news articles
- Company name resolution from `data/idx_stonks.csv`
- Smart filtering to avoid false positives from Indonesian words

### Supported Tickers
All stocks listed on IDX including:
- **Banking**: BBRI, BBCA, BMRI, BBNI, BNGA, etc.
- **Technology**: GOTO, BUKA, TLKM, EXCL, etc.
- **Consumer**: UNVR, INDF, ICBP, KLBF, etc.
- **Energy**: PGAS, ADRO, PTBA, ITMG, etc.
- And 900+ more...

## 🎯 Signal Generation Logic

### Signal Types

| Signal | Condition | Description |
|--------|-----------|-------------|
| **BUY** | `avg_sentiment > 0.3` | Strong positive sentiment |
| **SELL** | `avg_sentiment < -0.3` | Strong negative sentiment |
| **HOLD** | `-0.3 ≤ avg_sentiment ≤ 0.3` | Neutral or mixed sentiment |

### Signal Strength

Signal strength calculated from:
1. **Average sentiment score** (-1 to 1)
2. **Sentiment consistency** (lower std deviation = higher consistency)
3. Formula: `strength = |avg_sentiment| × consistency`

## 🧪 Testing

```bash
# Test scraper
python -c "from src.scraper.cnbc_scraper import CNBCScraper; s = CNBCScraper(); print(len(s.scrape_market_news(max_articles=5)))"

# Test sentiment analysis
python -c "from src.sentiment.analyzer import SentimentAnalyzer; a = SentimentAnalyzer(); print(a.analyze_text('Saham BBCA naik tajam hari ini'))"

# Test database
python main.py stats
```

## 🔧 Troubleshooting

### Issue: Models not downloading

```bash
# Pre-download models manually
python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; AutoTokenizer.from_pretrained('w11wo/indonesian-roberta-base-sentiment-classifier'); AutoModelForSequenceClassification.from_pretrained('w11wo/indonesian-roberta-base-sentiment-classifier')"
```

### Issue: Scraping fails

1. Check internet connection
2. Verify CNBC Indonesia website is accessible
3. Check `logs/scraper.log` for detailed errors
4. CNBC might have changed their HTML structure (update selectors in `cnbc_scraper.py`)

## ⚖️ Legal & Ethical Considerations

- ⚠️ Web scraping harus mematuhi `robots.txt` dan Terms of Service CNBC Indonesia
- ⚠️ Rate limiting sudah diimplementasikan (1 second delay antar request)
- ⚠️ Data yang di-scrape hanya untuk personal use atau research purposes
- ⚠️ **Bukan financial advice** - signals hanya untuk research/educational purposes

## 🛠️ Tech Stack

- **Python 3.10+**
- **Web Scraping**: Requests + BeautifulSoup4  
- **Database**: SQLite/Postgres + SQLAlchemy
- **Sentiment**: Transformers (HuggingFace) + IndoBERT
- **Stock Data**: 952 Indonesian stocks from IDX (idx_stonks.csv)
- **Scheduling**: APScheduler
- **Logging**: Loguru

## 📝 License

For educational and research purposes only.

## 🤝 Contributing

Feel free to:
- Report bugs
- Suggest features
- Improve documentation
- Optimize code

## 📧 Support

For questions or issues, check the logs at `logs/scraper.log` for detailed error messages.

---

**⚠️ Disclaimer**: This tool is for educational and research purposes only. Not financial advice. Always do your own research before making investment decisions.
