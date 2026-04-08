import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests_cache
from datetime import timedelta

# --- Architecture: Setup Caching to avoid Rate Limits ---
session = requests_cache.CachedSession('arth_sutra_cache', expire_after=timedelta(hours=1))

st.set_page_config(page_title="Arth Sutra: Wealth Engine", layout="wide")

# --- Styling ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #4e5d6e; }
    </style>
    """, unsafe_allow_html=True)

# --- Logic: The Engine Core ---
def get_stock_analysis(ticker_symbol):
    try:
        t = yf.Ticker(ticker_symbol, session=session)
        # Fetch 2 years to ensure 200 SMA is accurate
        df = t.history(period="2y")
        if df.empty or len(df) < 200:
            return None, None, None

        # 1. Technical Indicators
        df['SMA44'] = ta.sma(df['Close'], length=44)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        avg_vol = df['Volume'].tail(20).mean()

        curr = df.iloc[-1]
        
        # 2. Confidence Scoring (Bulletproof Logic)
        score = 0
        if curr['Close'] > curr['SMA200']: score += 40  # Trend Filter
        if abs(curr['Close'] - curr['SMA44']) / curr['SMA44'] < 0.02: score += 30 # Entry Zone
        if curr['Volume'] > (avg_vol * 1.5): score += 20 # Volume Confirmation
        if 40 < curr['RSI'] < 60: score += 10 # Momentum Strength

        # 3. Decision
        if score >= 80: status = "🚀 HIGH BULLISH"
        elif score >= 50: status = "⚖️ NEUTRAL / HOLD"
        else: status = "❌ AVOID / BEARISH"

        return df, t.info, status, score, t.news
    except Exception as e:
        return None, None, str(e), 0, None

# --- UI: Main Dashboard ---
st.title("🛡️ Arth Sutra: The Wealth Creation Engine")
st.subheader("Disciplined Investing for Financial Freedom")

# Common stock list for Nifty 200 (Sample)
nifty200 = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "TATAMOTORS.NS", "SBIN.NS", "ITC.NS", "INFY.NS", "ADANIENT.NS", "ZOMATO.NS"]

# Sidebar Selection
selected_stock = st.sidebar.selectbox("Select Stock for Deep-Dive Analysis", nifty200)

if st.sidebar.button("Nikalye Kundali"):
    with st.spinner(f"Analyzing {selected_stock}... Thinking like an Engineer."):
        df, info, status, score, news = get_stock_analysis(selected_stock)
        
        if df is not None:
            # --- Row 1: The Verdict ---
            st.divider()
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                st.metric("Price", f"₹{round(df['Close'].iloc[-1], 2)}")
            with col2:
                st.metric("Confidence Score", f"{score}%")
            with col3:
                st.header(f"Verdict: {status}")

            # --- Row 2: The Chart ---
            st.subheader("📈 Technical Chart (44/200 SMA Strategy)")
            st.line_chart(df[['Close', 'SMA44', 'SMA200']].tail(250))

            # --- Row 3: Kundali Details ---
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📑 Fundamental Kundali")
                fundamentals = {
                    "Company": info.get('longName'),
                    "PE Ratio": info.get('trailingPE'),
                    "Debt/Equity": info.get('debtToEquity'),
                    "ROE": f"{info.get('returnOnEquity', 0)*100:.2f}%",
                    "Profit Margin": f"{info.get('profitMargins', 0)*100:.2f}%"
                }
                st.json(fundamentals)
                st.write(f"**Business Summary:** {info.get('longBusinessSummary')[:600]}...")

            with c2:
                st.subheader("🗞️ Market Sentiment & News")
                if news:
                    for n in news[:5]:
                        st.info(f"**{n['title']}**\n\n*Source: {n['publisher']}*")
                else:
                    st.warning("No recent news found for this ticker.")
        else:
            st.error(f"Error fetching data: {status}")

# --- Footer Guidance ---
st.sidebar.divider()
st.sidebar.info("💡 **Engineer's Tip:** Target 1:2 Risk-Reward. Always keep an eye on Volume Surges near 44 SMA.")