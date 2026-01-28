"""
Streamlit Dashboard for CNBC News Sentiment Analysis
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import func, desc

from src.database.connection import get_db
from src.database.models import Article

# Page configuration
st.set_page_config(
    page_title="CNBC Market Sentiment Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_dashboard_data(timeframe_days: int):
    """Load data for dashboard"""
    with get_db() as db:
        # Calculate time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=timeframe_days)
        
        # Get articles with sentiment
        articles = db.query(Article).filter(
            Article.published_date >= start_date,
            Article.sentiment_label.isnot(None)  # Only articles with sentiment
        ).order_by(desc(Article.published_date)).all()
        
        # Get sentiment statistics
        sentiment_stats = db.query(
            func.count(Article.id).label('total'),
            func.avg(Article.sentiment_score).label('avg_sentiment'),
            func.count(Article.id).filter(Article.sentiment_label == 'positive').label('positive_count'),
            func.count(Article.id).filter(Article.sentiment_label == 'negative').label('negative_count'),
            func.count(Article.id).filter(Article.sentiment_label == 'neutral').label('neutral_count'),
        ).filter(
            Article.published_date >= start_date,
            Article.sentiment_label.isnot(None)
        ).first()
        
        return articles, sentiment_stats


def main():
    st.title("📈 CNBC Market Sentiment Analysis")
    st.markdown("Real-time sentiment analysis dari berita CNBC Indonesia Market")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        timeframe = st.selectbox(
            "Timeframe",
            options=[1, 7, 14, 30, 60, 90],
            index=1,
            format_func=lambda x: f"{x} hari" if x > 1 else "1 hari"
        )
        
        st.markdown("---")
        st.markdown("### 📊 Tentang Dashboard")
        st.markdown("""
        Dashboard ini menampilkan:
        - Sentiment analysis dari berita CNBC Indonesia Market
        - Trend sentiment dari waktu ke waktu
        - Statistik artikel positif/negatif/neutral
        """)
    
    # Load data
    with st.spinner("Loading data..."):
        articles, sentiment_stats = load_dashboard_data(timeframe)
    
    # Overview metrics
    st.header("📊 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Articles",
            value=sentiment_stats.total if sentiment_stats else 0
        )
    
    with col2:
        avg_sentiment = sentiment_stats.avg_sentiment if sentiment_stats and sentiment_stats.avg_sentiment else 0
        sentiment_emoji = "😊" if avg_sentiment > 0 else "😐" if avg_sentiment == 0 else "😟"
        st.metric(
            label="Avg Sentiment",
            value=f"{avg_sentiment:.2f} {sentiment_emoji}"
        )
    
    with col3:
        positive_count = sentiment_stats.positive_count if sentiment_stats else 0
        st.metric(
            label="Positive News",
            value=positive_count,
            delta="Bullish"
        )
    
    with col4:
        negative_count = sentiment_stats.negative_count if sentiment_stats else 0
        st.metric(
            label="Negative News",
            value=negative_count,
            delta="Bearish",
            delta_color="inverse"
        )
    
    # Sentiment distribution
    st.header("📈 Sentiment Distribution")
    
    if sentiment_stats and sentiment_stats.total > 0:
        sentiment_df = pd.DataFrame({
            'Sentiment': ['Positive', 'Neutral', 'Negative'],
            'Count': [
                sentiment_stats.positive_count,
                sentiment_stats.neutral_count,
                sentiment_stats.negative_count
            ]
        })
        
        fig_pie = px.pie(
            sentiment_df,
            values='Count',
            names='Sentiment',
            color='Sentiment',
            color_discrete_map={
                'Positive': '#00CC96',
                'Neutral': '#FFA15A',
                'Negative': '#EF553B'
            },
            hole=0.4
        )
        
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Belum ada data sentiment untuk timeframe ini")
    
    # Recent articles
    st.header("📰 Recent Articles")
    
    if articles:
        for article in articles[:10]:  # Show top 10
            with st.expander(f"{article.title}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Category:** {article.category or 'N/A'}")
                    st.markdown(f"**Author:** {article.author or 'N/A'}")
                    st.markdown(f"**Published:** {article.published_date.strftime('%d %b %Y, %H:%M') if article.published_date else 'N/A'}")
                    st.markdown(f"**Content:** {article.content[:300]}..." if article.content else "")
                    st.markdown(f"[Read full article]({article.url})")
                
                with col2:
                    sentiment_color = "#00CC96" if article.sentiment_label == 'positive' else "#EF553B" if article.sentiment_label == 'negative' else "#FFA15A"
                    st.markdown(f"<div style='background-color: {sentiment_color}; padding: 10px; border-radius: 5px; text-align: center;'>"
                              f"<b>{article.sentiment_label.upper() if article.sentiment_label else 'N/A'}</b><br>"
                              f"Score: {article.sentiment_score:.2f if article.sentiment_score else 0:.2f}<br>"
                              f"Confidence: {article.confidence:.1%if article.confidence else 0:.1%}"
                              f"</div>", unsafe_allow_html=True)
    else:
        st.info("Belum ada artikel. Jalankan scraper terlebih dahulu.")
    
    # Sentiment timeline
    if articles:
        st.header("📉 Sentiment Over Time")
        
        timeline_data = []
        for article in articles:
            if article.published_date and article.sentiment_label:
                timeline_data.append({
                    'date': article.published_date,
                    'sentiment': article.sentiment_score,
                    'label': article.sentiment_label
                })
        
        if timeline_data:
            timeline_df = pd.DataFrame(timeline_data)
            timeline_df = timeline_df.sort_values('date')
            
            fig_timeline = px.scatter(
                timeline_df,
                x='date',
                y='sentiment',
                color='label',
                color_discrete_map={
                    'positive': '#00CC96',
                    'neutral': '#FFA15A',
                    'negative': '#EF553B'
                },
                title='Sentiment Trend',
                labels={'date': 'Date', 'sentiment': 'Sentiment Score'}
            )
            
            # Add horizontal lines for thresholds
            fig_timeline.add_hline(y=0.3, line_dash="dash", line_color="green", annotation_text="Bullish threshold")
            fig_timeline.add_hline(y=-0.3, line_dash="dash", line_color="red", annotation_text="Bearish threshold")
            fig_timeline.add_hline(y=0, line_dash="dot", line_color="gray")
            
            fig_timeline.update_layout(height=400)
            st.plotly_chart(fig_timeline, use_container_width=True)


if __name__ == "__main__":
    main()
