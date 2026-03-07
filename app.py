import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- UI SETUP ---
st.set_page_config(page_title="Pro Scanner 2026", layout="wide")
st.title("🛡️ 44-200 SMA 'Bulletproof' Scanner")

# Expanded list including Hindalco and others
STOCK_LIST = ["HINDALCO.NS", "COALINDIA.NS", "ADANIPORTS.NS", "BEL.NS", 
              "TATAMOTORS.NS", "SBIN.NS", "RELIANCE.NS", "TCS.NS"]

def get_flat_data(ticker):
    try:
        # Download data
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        if data.empty:
            return None
            
        # FORCE FLATTEN: This fixes the "identically-labeled Series" error
        # We extract only the columns we need into a clean, new DataFrame
        clean_df = pd.DataFrame(index=data.index)
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in data.columns:
                # If MultiIndex, this grabs the column regardless of the ticker level
                clean_df[col] = data[col].values 
            
        return clean_df
    except Exception as e:
        st.error(f"Failed to fetch {ticker}: {e}")
        return None

def scan_market():
    matches = []
    for ticker in STOCK_LIST:
        df = get_flat_data(ticker)
        if df is None or len(df) < 200:
            continue
            
        # Standardize column names for pandas_ta
        df.columns = [x.lower() for x in df.columns]
        
        # Calculations
        df['sma44'] = ta.sma(df['close'], length=44)
        df['sma200'] = ta.sma(df['close'], length=200)
        
        last = df.iloc[-1]
        
        # --- STRATEGY LOGIC ---
        # 1. Trend: 44 SMA > 200 SMA
        # 2. Touch: Low is within 0.7% of the 44 SMA
        # 3. Bounce: Close is above the 44 SMA
        
        dist_from_44 = (last['low'] - last['sma44']) / last['sma44']
        
        if last['sma44'] > last['sma200'] and dist_from_44 <= 0.007 and last['close'] > last['sma44']:
            matches.append({
                "Ticker": ticker,
                "Price": round(last['close'], 2),
                "44 SMA": round(last['sma44'], 2),
                "Dist %": f"{round(dist_from_44 * 100, 2)}%",
                "Signal": "✅ Support Hit"
            })
    return matches

# --- EXECUTION ---
if st.button("▶ Run Friday Market Analysis"):
    with st.spinner("Analyzing market data..."):
        results = scan_market()
        
    if results:
        st.success(f"Found {len(results)} stocks matching your 44-SMA strategy!")
        st.dataframe(pd.DataFrame(results), use_container_width=True)
    else:
        st.info("No 'Perfect' hits found. This usually happens if Friday was a very weak day (Red candles).")
        st.write("Tip: Try adjusting the distance logic if you want to see 'Near Misses'.")
