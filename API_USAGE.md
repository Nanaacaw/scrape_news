# REST API Usage Guide

## 🚀 Quick Start

> Local dev defaults to SQLite via `DATABASE_PATH` (see `.env.example`). For deployment use Postgres via `DATABASE_URL` (see `.env.docker.example`).

### Start the API Server

```bash
# Development mode (auto-reload)
python -m src.api.main

#Or using uvicorn directly
uvicorn src.api.main:app --reload --port 8000
```

API will be available at: `http://localhost:8000`

### API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 📚 API Endpoints

### 1. Articles

#### Get Articles List
```bash
GET /api/articles?limit=10&ticker=BBRI&sentiment=positive
```

**Example Response:**
```json
{
  "total": 45,
  "limit": 10,
  "offset": 0,
  "articles": [
    {
      "id": 123,
      "title": "BBRI Bukukan Laba Rp50 Triliun",
      "url": "https://...",
      "source": "cnbc",
      "sentiment_score": 0.85,
      "sentiment_label": "positive",
      "tickers": ["BBRI"]
    }
  ]
}
```

#### Get Single Article
```bash
GET /api/articles/123
```

---

### 2. Sentiment Analysis

#### Sentiment Summary
```bash
GET /api/sentiment/summary?ticker=BBRI&days=7
```

**Example Response:**
```json
{
  "ticker": "BBRI",
  "period_days": 7,
  "total_articles": 25,
  "sentiment_distribution": {
    "positive": 15,
    "neutral": 7,
    "negative": 3
  },
  "avg_sentiment_score": 0.45
}
```

#### Sentiment Trend
```bash
GET /api/sentiment/trend?ticker=BBRI&days=30
```

#### Compare Multiple Tickers
```bash
GET /api/sentiment/compare?tickers=BBRI,BBCA,BMRI&days=7
```

---

### 3. Search

```bash
GET /api/search?q=inflasi&limit=20
```

---

### 4. Statistics

#### Overview
```bash
GET /api/stats/overview
```

#### Top Tickers
```bash
GET /api/stats/tickers?limit=10&days=30
```

---

## 🐍 Python Examples

### Using requests library

```python
import requests

BASE_URL = "http://localhost:8000"

# Get positive articles about BBRI
response = requests.get(f"{BASE_URL}/api/articles", params={
    "ticker": "BBRI",
    "sentiment": "positive",
    "limit": 10
})
data = response.json()

print(f"Found {data['total']} articles")
for article in data['articles']:
    print(f"- {article['title']} ({article['sentiment_score']})")

# Get sentiment trend
response = requests.get(f"{BASE_URL}/api/sentiment/trend", params={
    "ticker": "BBRI",
    "days": 30
})
trend = response.json()

print(f"Sentiment trend for {trend['ticker']}:")
for point in trend['data']:
    print(f"  {point['date']}: {point['avg_sentiment']}")

# Search articles
response = requests.get(f"{BASE_URL}/api/search", params={
    "q": "inflasi",
    "limit": 5
})
results = response.json()

print(f"Found {results['total']} articles about '{results['query']}'")
```

### Using httpx (async)

```python
import httpx
import asyncio

async def get_sentiment_data():
    async with httpx.AsyncClient() as client:
        # Multiple concurrent requests
        tasks = [
            client.get("http://localhost:8000/api/sentiment/summary?ticker=BBRI"),
            client.get("http://localhost:8000/api/sentiment/summary?ticker=BBCA"),
            client.get("http://localhost:8000/api/sentiment/summary?ticker=BMRI")
        ]
        
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

data = asyncio.run(get_sentiment_data())
for ticker_data in data:
    print(f"{ticker_data['ticker']}: {ticker_data['avg_sentiment_score']}")
```

---

## 🌐 JavaScript/TypeScript Examples

### Fetch API

```javascript
// Get articles
const response = await fetch('http://localhost:8000/api/articles?ticker=BBRI&limit=10');
const data = await response.json();

console.log(`Total articles: ${data.total}`);
data.articles.forEach(article => {
  console.log(`${article.title} - Sentiment: ${article.sentiment_label}`);
});

// Get trend data
const trendResponse = await fetch('http://localhost:8000/api/sentiment/trend?ticker=BBRI&days=30');
const trendData = await trendResponse.json();

// Plot using Chart.js or similar
const dates = trendData.data.map(d => d.date);
const sentiments = trendData.data.map(d => d.avg_sentiment);
```

### Axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
});

// Get positive BBRI articles
const { data } = await api.get('/articles', {
  params: {
    ticker: 'BBRI',
    sentiment: 'positive',
    limit: 10
  }
});

// Search
const searchResults = await api.get('/search', {
  params: { q: 'inflasi' }
});
```

---

## 🔧 Advanced Usage

### Filtering by Date Range

```bash
GET /api/articles?date_from=2024-01-01&date_to=2024-01-31&ticker=BBRI
```

### Pagination

```bash
# Page 1
GET /api/articles?limit=50&offset=0

# Page 2
GET /api/articles?limit=50&offset=50

# Page 3
GET /api/articles?limit=50&offset=100
```

### Health Check

```bash
GET /api/health
GET /api/stats/health  # With database check
```

---

## 🐛 Error Handling

API returns standard HTTP status codes:

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

**Example Error Response:**
```json
{
  "detail": "Article with id 999 not found"
}
```

**Python error handling:**
```python
try:
    response = requests.get(f"{BASE_URL}/api/articles/999")
    response.raise_for_status()
except requests.HTTPError as e:
    print(f"Error: {e.response.json()['detail']}")
```

---

## 🚀 Production Deployment

### Using Gunicorn + Uvicorn Workers

```bash
pip install gunicorn
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t news-api .
docker run -p 8000:8000 news-api
```

---

## 📊 Integrations

### Power BI / Tableau

Use the API as a data source:
- Connect to REST API
- Endpoint: `http://localhost:8000/api/articles`
- Refresh data on schedule

### Mobile Apps

Perfect for React Native, Flutter:
```typescript
// React Native example
const fetchArticles = async (ticker: string) => {
  const response = await fetch(`${API_URL}/api/articles?ticker=${ticker}`);
  const data = await response.json();
  return data.articles;
};
```

### Webhooks / Alerts

Build notification system:
```python
# Check new positive articles every hour
sentiment = api.get('/api/sentiment/summary?ticker=BBRI&days=1')
if sentiment['avg_sentiment_score'] > 0.7:
    send_alert("🎉 Very positive news about BBRI!")
```
