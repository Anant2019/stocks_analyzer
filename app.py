import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from concurrent.futures import ThreadPoolExecutor

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pro Stock Scanner", layout="wide")
st.title("🚀 Chartink-Style 44-200 SMA Scanner")

# --- STEP 1: DEFINE LARGE WATCHLIST ---
# You can add more .NS tickers here to scan the whole market
WATCHLIST = [
    "HINDALCO.NS", "RELIANCE.NS", "TCS.NS", "INFY.NS", "TATAMOTORS.NS", 
    "BEL.NS", "ADANIENT.NS", "SBIN.NS", "ICICIBANK.NS", "BHARTIARTL.NS",
    "HAL.NS", "COALINDIA.NS", "NTPC.NS", "ITC.NS", "JSWSTEEL.NS"
]

# --- STEP 2: THE SCANNING ENGINE ---
def scan_stock(symbol, strict_green, sma_buffer):
    try:
        df = yf.download(symbol, period="2y", interval="1d", progress=False)
        if df.empty or len(df) < 200: return None
        
        # Clean Multi-Index Headers
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Indicators
        df['sma44'] = ta.sma(df['Close'], length=44)
        df['sma200'] = ta.sma(df['Close'], length=200)
        
        curr = df.iloc[-1]
        prev_44 = df['sma44'].iloc[-5] # Check if SMA 44 is rising over last week

        # Strategy Logic
        is_trending = curr['sma44'] > curr['sma200'] and curr['sma44'] > prev_44
        
        # Touch logic with user-defined buffer (e.g., within 0.5% of SMA)
        is_touching = curr['Low'] <= (curr['sma44'] * (1 + sma_buffer/100))
        
        # Candle Color Logic
        is_bullish = True
        if strict_green:
            is_bullish = curr['Close'] > curr['Open']

        if is_trending and is_touching and is_bullish:
            return {
                "Ticker": symbol,
                "Price": round(float(curr['Close']), 2),
                "44 SMA": round(float(curr['sma44']), 2),
                "Dist %": round(((curr['Low'] - curr['sma44'])/curr['sma44'])*100, 2),
                "Candle": "🟢" if curr['Close'] > curr['Open'] else "🔴"
            }
    except:
        return None
    return None

# --- STEP 3: SIDEBAR FILTERS (Like Chartink) ---
st.sidebar.header("Filter Settings")
strict_green = st.sidebar.checkbox("Strict Green Candle Only", value=True)
sma_buffer = st.sidebar.slider("SMA Touch Buffer (%)", 0.0, 2.0, 0.2)
threads = st.sidebar.slider("Scan Speed (Threads)", 1, 20, 10)

# --- STEP 4: EXECUTION ---
if st.button("▶ Run Full Market Scan"):
    results = []
    st.write(f"Scanning {len(WATCHLIST)} stocks...")
    progress = st.progress(0)
    
    # Using ThreadPoolExecutor to scan stocks in parallel (Super Fast)
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(scan_stock, s, strict_green, sma_buffer) for s in WATCHLIST]
        for i, future in enumerate(futures):
            res = future.result()
            if res:
                results.append(res)
            progress.progress((i + 1) / len(WATCHLIST))

    if results:
        st.success(f"Found {len(results)} Matches!")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.warning("No matches found. Try increasing the 'SMA Touch Buffer' or unchecking 'Strict Green Candle'.")
