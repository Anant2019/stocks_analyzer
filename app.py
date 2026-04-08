import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="Arth Sutra: Wealth Engine", layout="wide")

def judge_stock(symbol):
    t = yf.Ticker(symbol)
    df = t.history(period="1y")
    if df.empty or len(df) < 200: return None

    # Technical Calculations
    df['SMA44'] = ta.sma(df['Close'], length=44)
    df['SMA200'] = ta.sma(df['Close'], length=200)
    df['RSI'] = ta.rsi(df['Close'], length=14)
    avg_vol = df['Volume'].tail(20).mean()

    curr = df.iloc[-1]
    
    # 1. Trend Analysis
    is_long_term_up = curr['Close'] > curr['SMA200']
    is_near_44 = abs(curr['Close'] - curr['SMA44']) / curr['SMA44'] < 0.02
    volume_surge = curr['Volume'] > (avg_vol * 1.3)
    
    # 2. Assign Condition & Confidence
    confidence = 0
    if is_long_term_up: confidence += 40
    if is_near_44: confidence += 30
    if volume_surge: confidence += 20
    if 40 < curr['RSI'] < 60: confidence += 10

    if confidence >= 80:
        status = "🚀 HIGH BULLISH"
    elif confidence >= 50:
        status = "⚖️ NEUTRAL / HOLD"
    else:
        status = "❌ AVOID / BEARISH"

    return {
        "Ticker": symbol,
        "Price": round(curr['Close'], 2),
        "Confidence %": confidence,
        "Condition": status,
        "RSI": round(curr['RSI'], 1),
        "Volume": "High" if volume_surge else "Normal"
    }

# --- Main Dashboard ---
st.title("🛡️ Arth Sutra Wealth Engine: Nifty 200 Report")

# For now, using a sample. In your real tool, load the full Nifty 200 CSV.
tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "TATAMOTORS.NS", "ITC.NS", "ADANIENT.NS", "SBIN.NS"]

all_data = []
for s in tickers:
    result = judge_stock(s)
    if result: all_data.append(result)

report_df = pd.DataFrame(all_data)

# --- Filters ---
st.sidebar.header("Filter Engine")
filter_status = st.sidebar.multiselect("Select Conditions to Show", 
                                       options=["🚀 HIGH BULLISH", "⚖️ NEUTRAL / HOLD", "❌ AVOID / BEARISH"],
                                       default=["🚀 HIGH BULLISH", "⚖️ NEUTRAL / HOLD", "❌ AVOID / BEARISH"])

filtered_df = report_df[report_df['Condition'].isin(filter_status)]

# --- Display Logic ---
st.subheader("Live Market Judgment")
st.dataframe(filtered_df.sort_values(by="Confidence %", ascending=False), use_container_width=True)

# Detailed Insights on Selection
selected = st.selectbox("Deep Dive into Stock Fundamentals & News", filtered_df['Ticker'])
if selected:
    st.divider()
    t_obj = yf.Ticker(selected)
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"### {selected} Technical Chart")
        st.line_chart(t_obj.history(period="6mo")['Close'])
    with col2:
        st.write("### Fundamental & Sentiment Analysis")
        st.json(t_obj.info) # Detailed stats like PE, Debt, Growth
        st.write("#### Latest News")
        for n in t_obj.news[:3]:
            st.write(f"- {n['title']}")