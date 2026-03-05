import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="ArthaSutra | Adaptive Strategist", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    .regime-card {
        background-color: #161A23; border: 1px solid #2D3436; border-radius: 12px;
        padding: 20px; margin-bottom: 20px; border-left: 10px solid;
    }
    .trend-glow { border-left-color: #00FFA3; box-shadow: 0 0 15px rgba(0, 255, 163, 0.2); }
    .choppy-glow { border-left-color: #FFC107; box-shadow: 0 0 15px rgba(255, 193, 7, 0.2); }
    .volatile-glow { border-left-color: #FF4B4B; box-shadow: 0 0 15px rgba(255, 75, 75, 0.2); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE ADAPTIVE STRATEGIST ENGINE ---
def run_regime_audit(ticker, target_date):
    try:
        # Fetch data with buffer for indicators
        df = yf.download(ticker, start=target_date - timedelta(days=400), end=target_date + timedelta(days=5), auto_adjust=True, progress=False)
        if df.empty or len(df) < 200: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        # 1. CORE INDICATORS
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # Bollinger Bands (Regime Detection)
        df['STD'] = df['Close'].rolling(20).std()
        df['BB_UP'] = df['EMA20'] + (df['STD'] * 2)
        df['BB_LOW'] = df['EMA20'] - (df['STD'] * 2)
        
        # ATR (Volatility Check)
        high_low = df['High'] - df['Low']
        high_cp = np.abs(df['High'] - df['Close'].shift())
        low_cp = np.abs(df['Low'] - df['Close'].shift())
        df['ATR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1).rolling(14).mean()
        df['ATR_AVG'] = df['ATR'].rolling(20).mean()

        # RSI (Prior Feature & Trigger)
        delta = df['Close'].diff(); gain = delta.where(delta > 0, 0).rolling(14).mean(); loss = -delta.where(delta < 0, 0).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

        # Target Row
        v_dates = df.index[df.index.date <= target_date]
        if v_dates.empty: return None
        d = df.loc[v_dates[-1]]
        
        # --- PHASE 1: REGIME DETECTION ---
        is_volatile = d['ATR'] > (d['ATR_AVG'] * 2)
        is_trending = (d['Close'] > d['BB_UP'] or d['Close'] < d['BB_LOW']) and abs(d['EMA200'] - df['EMA200'].shift(5).loc[v_dates[-1]]) > 0.1
        is_choppy = not is_trending and not is_volatile

        regime = "TRENDING" if is_trending else "VOLATILE" if is_volatile else "CHOPPY"
        
        # --- PHASE 2: ADAPTIVE LOGIC ---
        signal = {"action": "WAIT", "entry": 0.0, "sl": 0.0, "tp_1_1": 0.0, "tp_1_2": 0.0}
        strategy = "Neutral"
        logic_bridge = "Market volatility too high for safe capital deployment."

        if regime == "TRENDING":
            strategy = "Trend Follower"
            # Buy Pullback to 20 EMA
            if d['Low'] <= d['EMA20'] * 1.01 and d['Close'] > d['EMA20']:
                signal['action'] = "BUY"
                signal['entry'] = round(float(d['Close']), 2)
                signal['sl'] = round(float(d['Low'] * 0.99), 2)
                risk = signal['entry'] - signal['sl']
                signal['tp_1_1'] = round(signal['entry'] + risk, 2)
                signal['tp_1_2'] = round(signal['entry'] + (risk * 2), 2)
                logic_bridge = "Strong trend found. Buying the EMA 20 pullback for a 1:2 RRR ride."

        elif regime == "CHOPPY":
            strategy = "Mean Reversion"
            # Buy Oversold / Sell Overbought
            if d['RSI'] < 35:
                signal['action'] = "BUY"
                signal['entry'] = round(float(d['Close']), 2)
                signal['sl'] = round(float(d['Low'] * 0.985), 2)
                risk = signal['entry'] - signal['sl']
                signal['tp_1_1'] = round(signal['entry'] + risk, 2)
                signal['tp_1_2'] = round(signal['entry'] + (risk * 2), 2)
                logic_bridge = "Range-bound market. RSI oversold trigger active for quick 1:1 profit."

        return {
            "detected_regime": regime,
            "recommended_strategy": strategy,
            "trade_signal": signal,
            "confidence_score": "75%" if signal['action'] != "WAIT" else "0%",
            "logic_bridge": logic_bridge,
            "ticker": ticker
        }
    except Exception as e: return None

# --- UI ---
st.title("💹 ArthaSutra | Adaptive Regime Strategist")
st.sidebar.header("Scan Parameters")
audit_date = st.sidebar.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
tickers = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'SBIN.NS', 'AXISBANK.NS', 'TITAN.NS']

if st.button("🚀 EXECUTE REGIME ANALYSIS"):
    results = []
    for t in tickers:
        res = run_regime_audit(t, audit_date)
        if res: results.append(res)
    
    if results:
        for r in results:
            glow = "trend-glow" if r['detected_regime'] == "TRENDING" else "choppy-glow" if r['detected_regime'] == "CHOPPY" else "volatile-glow"
            
            st.markdown(f"""
            <div class="regime-card {glow}">
                <h3>{r['ticker']} | {r['detected_regime']}</h3>
                <p><b>Strategy:</b> {r['recommended_strategy']} | <b>Confidence:</b> {r['confidence_score']}</p>
                <pre style="background: #000; color: #00FFA3; padding: 15px; border-radius: 8px;">{json.dumps(r, indent=2)}</pre>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.error("Data fetch error. Check internet or Ticker symbols.")
