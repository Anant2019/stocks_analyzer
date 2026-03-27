import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

# 1. Page Config & Persistence Logic
st.set_page_config(page_title="Arth Sutra | Success Tracker", layout="wide")

# This keeps your data from "vanishing" when you click other buttons
if 'results' not in st.session_state:
    st.session_state.results = []
if 'win_rate' not in st.session_state:
    st.session_state.win_rate = 0

st.markdown("""
    <style>
    .main { background-color: #050505; color: white; }
    .card { background: #111; border: 1px solid #333; border-radius: 12px; padding: 20px; margin-bottom: 20px; border-top: 4px solid #444; }
    .success { color: #00FF41; font-weight: bold; }
    .fail { color: #ff4b4b; font-weight: bold; }
    .metric-box { background: #1a1a1a; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# 2. Sidebar Controls
st.sidebar.header("🕹️ Backtest Control")
test_date = st.sidebar.date_input("Pick a Past Date to Analyze", value=datetime.now() - timedelta(days=20))
forward_window = st.sidebar.slider("Days to track success", 5, 30, 10)

# 3. The Analysis Engine (Fixed for 2024/2025 yfinance format)
def run_backtest(symbol, target_date):
    try:
        # Fetch extra data to cover both the indicators and the forward look
        start_date = target_date - timedelta(days=150)
        end_date = target_date + timedelta(days=forward_window + 5)
        
        # FIX: auto_adjust=True and manual column flattening
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        if data.empty: return None
        
        # Flatten Multi-Index columns if they exist
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Split into "Knowledge" (Past) and "Outcome" (Future)
        past = data[:target_date].copy()
        future = data[target_date:].copy()

        if len(past) < 50 or future.empty: return None

        # Calculate Technicals
        past['EMA20'] = ta.ema(past['Close'], length=20)
        past['EMA50'] = ta.ema(past['Close'], length=50)
        past['RSI'] = ta.rsi(past['Close'], length=14)

        curr = past.iloc[-1]
        entry_price = float(curr['Close'])
        
        # Scoring Logic
        score = 0
        if entry_price > curr['EMA50']: score += 40
        if entry_price <= curr['EMA20'] * 1.02: score += 35
        if 40 < curr['RSI'] < 65: score += 25

        # Track what happened next
        peak_price = future['High'].max()
        low_price = future['Low'].min()
        
        # Logic: 5% Target vs 3% Stop Loss
        target = entry_price * 1.05
        stop = entry_price * 0.97
        
        status = "HOLDING"
        if peak_price >= target: status = "✅ SUCCESS"
        elif low_price <= stop: status = "❌ STOP LOSS"

        return {
            "Symbol": symbol.replace(".NS", ""),
            "Score": score,
            "Entry": round(entry_price, 2),
            "Outcome": status,
            "MaxGain": round(((peak_price - entry_price)/entry_price)*100, 2)
        }
    except Exception as e:
        return None

# 4. Main UI
st.title("🏹 ARTH SUTRA | Success Rate Tracer")

WATCHLIST = ["RELIANCE.NS", "TCS.NS", "BHARTIARTL.NS", "HAL.NS", "BEL.NS", "INFY.NS", "ICICIBANK.NS", "SBIN.NS", "HDFCBANK.NS"]

if st.button("🚀 TRACE SUCCESS RATE"):
    with st.spinner(f"Analyzing trades from {test_date}..."):
        results = [run_backtest(s, test_date) for s in WATCHLIST]
        st.session_state.results = [r for r in results if r and r['Score'] >= 75]
        
        # Calculate Win Rate
        if st.session_state.results:
            wins = len([r for r in st.session_state.results if "SUCCESS" in r['Outcome']])
            st.session_state.win_rate = round((wins / len(st.session_state.results)) * 100, 2)

# Display Results
if st.session_state.results:
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Setups Found", len(st.session_state.results))
    c2.metric("Win Rate", f"{st.session_state.win_rate}%")
    c3.metric("Market Date", str(test_date))
    
    st.write("### Individual Trade Performance")
    grid = st.columns(3)
    for idx, res in enumerate(st.session_state.results):
        with grid[idx % 3]:
            color = "#00FF41" if "SUCCESS" in res['Outcome'] else "#ff4b4b"
            st.markdown(f"""
            <div class="card" style="border-top-color: {color}">
                <h2 style="margin:0;">{res['Symbol']}</h2>
                <p>Score: <b>{res['Score']}%</b></p>
                <p>Entry Price: ₹{res['Entry']}</p>
                <h3 style="color:{color}">{res['Outcome']}</h3>
                <p style="font-size:0.8rem; color:#888;">Max Move in window: {res['MaxGain']}%</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No data yet. Select a date in the sidebar and click 'Trace' to begin.")