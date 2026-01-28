# CNBC Market Scraping + Sentiment Analysis

> **Stock screening system** yang mengintegrasikan web scraping dari CNBC Indonesia dengan sentiment analysis menggunakan IndoBERT untuk mendukung keputusan investasi.

## 📋 Features

- 🌐 **Web Scraping**: Otomatis scrape berita market & investment dari CNBC Indonesia
- 🤖 **Sentiment Analysis**: Analisis sentiment menggunakan IndoBERT (Bahasa Indonesia)
- 📊 **Stock Screening**: Generate BUY/SELL/HOLD signals berdasarkan sentiment
- 📈 **Interactive Dashboard**: Real-time visualization dengan Streamlit
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
# Scrape all categories (market + investment)
python main.py scrape --limit 10 --generate-signals

# Atau scrape specific category:
# python main.py scrape --category market --limit 20
```

### 5. Launch Dashboard

```bash
python main.py dashboard

# Atau langsung:
# streamlit run src/dashboard/app.py
```

Dashboard akan terbuka di browser: `http://localhost:8501`

## 📖 Usage Guide

### CLI Commands

```bash
# Initialize database
python main.py init

# Scrape news articles
python main.py scrape --category all --limit 50 --generate-signals

# Run sentiment analysis on existing articles
python main.py analyze

# Generate screening signals
python main.py screen --show --limit 10

# Show database statistics
python main.py stats

# Launch dashboard
python main.py dashboard
```

### Scraping Options

| Category | URL | Description |
|----------|-----|-------------|
| `market` | cnbcindonesia.com/market | Market news & analysis |
| `investment` | cnbcindonesia.com/investment | Investment tips & insights |
| `all` | Both categories | Comprehensive coverage |

### Automated Scheduling

Untuk menjalankan scraping otomatis sesuai interval:

```bash
python src/scraper/scheduler.py
```

Default: scrape setiap **1 jam** (bisa diatur di `.env`)

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
│   ├── screening/
│   │   └── screener.py         # Stock screening logic
│   │
│   ├── pipeline/
│   │   └── data_pipeline.py    # Data processing pipeline
│   │
│   ├── dashboard/
│   │   └── app.py              # Streamlit dashboard
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

## ⚙️ Configuration

Edit `.env` file untuk customize behavior:

```bash
# Scraping
SCRAPE_INTERVAL_HOURS=1          # Interval untuk automated scraping
MAX_ARTICLES_PER_SCRAPE=50       # Max articles per scraping session
REQUEST_TIMEOUT=30               # HTTP request timeout (seconds)

# Sentiment Analysis
SENTIMENT_MODEL=indobenchmark/indobert-base-p1
SENTIMENT_BATCH_SIZE=8           # Batch size untuk sentiment analysis

# Screening
MIN_SENTIMENT_SCORE=0.3          # Minimum sentiment untuk signal
MIN_ARTICLES_FOR_SIGNAL=3        # Minimum articles untuk generate signal
SIGNAL_TIMEFRAME_DAYS=7          # Timeframe untuk screening (days)

# Logging
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
```

## 📊 Dashboard Features

### Overview Metrics
- Total articles scraped
- Average sentiment score
- Positive/negative news count

### Sentiment Distribution
- Pie chart showing sentiment breakdown
- Positive, neutral, negative percentages

### Screening Signals
- **BUY signals**: Stocks with strong positive sentiment
- **SELL signals**: Stocks with strong negative sentiment
- Signal strength and confidence metrics

### Recent Articles
- Latest news with sentiment analysis
- Direct links to original articles
- Category and author information

### Sentiment Timeline
- Trend analysis over time
- Interactive charts with thresholds
- Bullish/bearish indicators

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
- **Dashboard**: Streamlit + Plotly
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
