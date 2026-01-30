# CNBC Market Scraping + Sentiment Analysis

> **News sentiment analysis system** yang mengintegrasikan web scraping dari CNBC Indonesia & Bloomberg Technoz dengan sentiment analysis menggunakan IndoBERT untuk analisis berita pasar.

## 📋 Features

- 🌐 **Web Scraping**: Otomatis scrape berita dari CNBC Indonesia & Bloomberg Technoz
- 🤖 **Sentiment Analysis**: Analisis sentiment menggunakan IndoBERT (Bahasa Indonesia)
- 📈 **Stock Ticker Database**: Integrasi lengkap dengan 952 saham Indonesia dari IDX
- ⏰ **Automated Scheduling**: Scraping otomatis dengan interval yang bisa dikustomisasi
- 💾 **Database**: Penyimpanan data dengan SQLite

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
cd c:\Users\midory\Kerja\scrape_news

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
copy .env.example .env

# Edit .env sesuai kebutuhan (optional)
# Secara default sudah dikonfigurasi untuk scrape CNBC Indonesia
```

### 3. Initialize Database

```bash
python main.py init
```

### 4. Run First Scrape

```bash
# Scrape from both CNBC and Bloomberg
python main.py scrape --source all --limit 10

# Or scrape specific source:
# python main.py scrape --source cnbc --limit 20
# python main.py scrape --source bloomberg --limit 20
```

## 📖 Usage Guide

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
| `cnbc` | cnbcindonesia.com/market | CNBC Indonesia Market news |
| `bloomberg` | bloombergtechnoz.com/indeks/market | Bloomberg Technoz Market news |
| `all` | Both sources | Comprehensive coverage |

### Automated Scheduling

Untuk menjalankan scraping otomatis sesuai interval:

```bash
python src/scraper/scheduler.py
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
│  SQLite DB      │
│  - Articles     │
│  - Sentiments   │
│  - Stocks       │
│  - Signals      │
└────┬──────┬─────┘
     │      │
     │      └──────────────┐
     ▼                     ▼
┌──────────────┐   ┌──────────────────┐
│  Sentiment   │   │ Stock Screener   │
│   Analyzer   │──▶│  & Signals       │
│  (IndoBERT)  │   │  Generator       │
└──────────────┘   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │   Streamlit      │
                   │   Dashboard      │
                   └──────────────────┘
```

## 📁 Project Structure

```
scrape_news/
├── main.py                      # CLI entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore
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
│   ├── dashboard/
│   │   └── app.py              # Streamlit dashboard (REMOVED)
│   │
│   └── utils/
│       ├── config.py           # Configuration
│       ├── logger.py           # Logging
│       └── helpers.py          # Helper functions
│
├── data/                        # SQLite database (auto-created)
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

### Issue: Dashboard not showing data

1. Ensure database is initialized: `python main.py init`
2. Run scraper first: `python main.py scrape --limit 10`
3. Check if database file exists: `data/cnbc_news.db`

## ⚖️ Legal & Ethical Considerations

- ⚠️ Web scraping harus mematuhi `robots.txt` dan Terms of Service CNBC Indonesia
- ⚠️ Rate limiting sudah diimplementasikan (1 second delay antar request)
- ⚠️ Data yang di-scrape hanya untuk personal use atau research purposes
- ⚠️ **Bukan financial advice** - signals hanya untuk research/educational purposes

## 🛠️ Tech Stack

- **Python 3.9+**
- **Web Scraping**: Requests + BeautifulSoup4  
- **Database**: SQLite + SQLAlchemy
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
