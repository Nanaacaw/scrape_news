from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.api.routes import articles, sentiment, search, stats, feedback
from src.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="News Sentiment Analysis API",
    description="REST API for news articles with sentiment analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router)
app.include_router(sentiment.router)
app.include_router(search.router)
app.include_router(stats.router)
app.include_router(feedback.router)

@app.get("/", include_in_schema=False)
def root():
    """Redirect to API documentation"""
    return RedirectResponse(url="/docs")

@app.get("/api/health")
def health():
    """Quick health check without database"""
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting News Sentiment Analysis API...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
