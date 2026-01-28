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
from src.database.models import Article, Sentiment, Stock, ScreeningSignal, ArticleStock
from src.utils.config import SIGNAL_TIMEFRAME_DAYS

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
        articles = db.query(Article, Sentiment).join(Sentiment).filter(
            Article.published_date >= start_date
        ).order_by(desc(Article.published_date)).all()
        
        # Get latest screening signals
        signals = db.query(ScreeningSignal, Stock).join(Stock).order_by(
            desc(ScreeningSignal.signal_strength)
        ).limit(50).all()
        
        # Get sentiment statistics
        sentiment_stats = db.query(
            func.count(Sentiment.id).label('total'),
            func.avg(Sentiment.sentiment_score).label('avg_sentiment'),
            func.count(Sentiment.id).filter(Sentiment.sentiment_label == 'positive').label('positive_count'),
            func.count(Sentiment.id).filter(Sentiment.sentiment_label == 'negative').label('negative_count'),
            func.count(Sentiment.id).filter(Sentiment.sentiment_label == 'neutral').label('neutral_count'),
        ).join(Article).filter(
            Article.published_date >= start_date
        ).first()
        
        return articles, signals, sentiment_stats


def main():
    st.title("📈 CNBC Market Sentiment Analysis & Stock Screening")
    st.markdown("Real-time sentiment analysis dari berita CNBC Indonesia untuk stock screening")
    
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
        - Sentiment analysis dari berita CNBC Indonesia
        - Screening signals untuk saham
        - Trend sentiment dari waktu ke waktu
        - Top stocks berdasarkan sentiment
        """)
    
    # Load data
    with st.spinner("Loading data..."):
        articles, signals, sentiment_stats = load_dashboard_data(timeframe)
    
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
    
    # Screening signals
    st.header("🎯 Stock Screening Signals")
    
    if signals:
        # Filter tabs
        tab_all, tab_buy, tab_sell = st.tabs(["All Signals", "🟢 BUY", "🔴 SELL"])
        
        with tab_all:
            display_signals(signals, None)
        
        with tab_buy:
            buy_signals = [(sig, stock) for sig, stock in signals if sig.signal_type == 'BUY']
            display_signals(buy_signals, 'BUY')
        
        with tab_sell:
            sell_signals = [(sig, stock) for sig, stock in signals if sig.signal_type == 'SELL']
            display_signals(sell_signals, 'SELL')
    else:
        st.info("Belum ada screening signals. Jalankan scraper terlebih dahulu.")
    
    # Recent articles
    st.header("📰 Recent Articles")
    
    if articles:
        for article, sentiment in articles[:10]:  # Show top 10
            with st.expander(f"{article.title}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Category:** {article.category or 'N/A'}")
                    st.markdown(f"**Author:** {article.author or 'N/A'}")
                    st.markdown(f"**Published:** {article.published_date.strftime('%d %b %Y, %H:%M') if article.published_date else 'N/A'}")
                    st.markdown(f"**Summary:** {article.summary[:300]}..." if article.summary else "")
                    st.markdown(f"[Read full article]({article.url})")
                
                with col2:
                    sentiment_color = "#00CC96" if sentiment.sentiment_label == 'positive' else "#EF553B" if sentiment.sentiment_label == 'negative' else "#FFA15A"
                    st.markdown(f"<div style='background-color: {sentiment_color}; padding: 10px; border-radius: 5px; text-align: center;'>"
                              f"<b>{sentiment.sentiment_label.upper()}</b><br>"
                              f"Score: {sentiment.sentiment_score:.2f}<br>"
                              f"Confidence: {sentiment.confidence:.1%}"
                              f"</div>", unsafe_allow_html=True)
    else:
        st.info("Belum ada artikel. Jalankan scraper terlebih dahulu.")
    
    # Sentiment timeline
    if articles:
        st.header("📉 Sentiment Over Time")
        
        timeline_data = []
        for article, sentiment in articles:
            if article.published_date:
                timeline_data.append({
                    'date': article.published_date,
                    'sentiment': sentiment.sentiment_score,
                    'label': sentiment.sentiment_label
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


def display_signals(signals, signal_type=None):
    """Display screening signals in a table"""
    if not signals:
        st.info(f"No {signal_type or 'signals'} found")
        return
    
    signal_data = []
    for signal, stock in signals:
        signal_data.append({
            'Ticker': stock.ticker,
            'Company': stock.company_name or 'N/A',
            'Signal': signal.signal_type,
            'Strength': f"{signal.signal_strength:.2f}",
            'Avg Sentiment': f"{signal.avg_sentiment:.2f}",
            'Articles': signal.article_count,
            'Timeframe': f"{signal.timeframe_days}d",
            'Generated': signal.generated_date.strftime('%d %b %Y')
        })
    
    df = pd.DataFrame(signal_data)
    
    # Color code signals
    def color_signal(val):
        if val == 'BUY':
            return 'background-color: #d4edda'
        elif val == 'SELL':
            return 'background-color: #f8d7da'
        else:
            return 'background-color: #fff3cd'
    
    styled_df = df.style.applymap(color_signal, subset=['Signal'])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
