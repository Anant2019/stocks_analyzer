import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

# 1. UI Configuration
st.set_page_config(page_title="Arth Sutra | Backtest Engine", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; color: white; }
    .card { background: #111; border: 1px solid #333; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
    .success { color: #00FF41; font-weight: bold; border-left: 4px solid #00FF41; padding-left: 10px; }
    .fail { color: #ff4b4b; font-weight: bold; border-left: 4px solid #ff4b4b; padding-left: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Sidebar for Date Control
st.sidebar.header("🛠️ Backtest Settings")
# Default to 10 days ago to ensure we have "forward" data to check success
default_date = datetime.now() - timedelta(days=15)
selected_date = st.sidebar.date_input("Analysis Date", value=default_date)
look_forward_days = st.sidebar.slider("Check success after (days)", 1, 15, 7)

st.title("🏹 ARTH SUTRA | Historical Analyzer")
st.caption(f"Analyzing market state as of: {selected_date}")

# 3. Enhanced Analysis with Success Check
def analyze_historical(symbol, target_date):
    try:
        # Download data up to the "look forward" period
        end_fetch = target_date + timedelta(days=look_forward_days + 5)
        df = yf.download(symbol, start=(target_date - timedelta(days=100)), end=end_fetch, progress=False, multi_level_index=False)
        
        if df.empty: return None

        # Split data into "Past" (what the scanner saw) and "Future" (what happened after)
        past_data = df[:target_date].copy()
        future_data = df[target_date:].copy()

        if len(past_data) < 50 or future_data.empty:
            return None

        # Indicators on past data
        past_data['EMA20'] = ta.ema(past_data['Close'], length=20)
        past_data['EMA50'] = ta.ema(past_data['Close'], length=50)
        past_data['RSI'] = ta.rsi(past_data['Close'], length=14)
        
        curr = past_data.iloc[-1]
        price_at_scan = float(curr['Close'])
        
        # Strategy Logic
        score = 0
        if price_at_scan > curr['EMA50']: score += 40
        if price_at_scan <= curr['EMA20'] * 1.015: score += 35
        if 45 < curr['RSI'] < 65: score += 25

        # SUCCESS CHECK: Did price hit +5% before hitting -3% SL in the forward window?
        target_price = price_at_scan * 1.05
        sl_price = price_at_scan * 0.97
        
        max_future = future_data['High'].max()
        min_future = future_data['Low'].min()
        
        hit_target = max_future >= target_price
        hit_sl = min_future <= sl_price
        
        result_status = "PENDING"
        if hit_target: result_status = "SUCCESS"
        elif hit_sl: result_status = "STOP LOSS"

        return {
            "Symbol": symbol.replace(".NS", ""),
            "Price": round(price_at_scan, 2),
            "Score": score,
            "Status": result_status,
            "Max_Move": round(((max_future - price_at_scan)/price_at_scan)*100, 2)
        }
    except:
        return None

WATCHLIST = ["RELIANCE.NS", "TCS.NS", "BHARTIARTL.NS", "HAL.NS", "BEL.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS"]

if st.button("🔍 Run Historical Trace"):
    results = [analyze_historical(s, selected_date) for s in WATCHLIST]
    valid = [r for r in results if r and r['Score'] >= 75]

    if not valid:
        st.warning(f"No high-conviction setups were found on {selected_date}.")
    else:
        # Calculate Win Rate
        wins = len([r for r in valid if r['Status'] == "SUCCESS"])
        win_rate = (wins / len(valid)) * 100
        
        st.subheader(f"📊 Backtest Results (Win Rate: {win_rate}%)")
        
        cols = st.columns(3)
        for i, res in enumerate(valid):
            with cols[i % 3]:
                status_class = "success" if res['Status'] == "SUCCESS" else "fail"
                st.markdown(f"""
                <div class="card">
                    <h3>{res['Symbol']}</h3>
                    <p class="buy">Scan Score: {res['Score']}%</p>
                    <p>Price then: ₹{res['Price']}</p>
                    <p class="{status_class}">Outcome: {res['Status']}</p>
                    <p style="font-size:0.8rem">Max Peak: +{res['Max_Move']}%</p>
                </div>
                """, unsafe_allow_html=True)