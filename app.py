import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Nifty 500 Bullish Scanner", layout="wide")

def get_last_trading_day():
    """Handles Saturday/Sunday by returning Friday's date"""
    today = datetime.now()
    if today.weekday() == 5: # Saturday
        return today - timedelta(days=1)
    elif today.weekday() == 6: # Sunday
        return today - timedelta(days=2)
    return today

def get_nifty500_tickers():
    """Fetch the latest Nifty 500 list from NSE"""
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        df = pd.read_csv(url)
        return [f"{s}.NS" for s in df['Symbol'].tolist()]
    except:
        st.error("NSE Server busy. Using a fallback list.")
        return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "TATAMOTORS.NS"]

def scan_stocks(tickers):
    bullish_stocks = []
    progress_bar = st.progress(0)
    total = len(tickers)
    
    for i, ticker in enumerate(tickers):
        try:
            # Update progress bar every 10 stocks for speed
            if i % 10 == 0:
                progress_bar.progress((i + 1) / total)
            
            data = yf.download(ticker, period="1y", interval="1d", progress=False)
            if len(data) < 200: continue
            
            # Calculate Indicators
            df = data.copy()
            df['SMA44'] = df['Close'].rolling(window=44).mean()
            df['SMA200'] = df['Close'].rolling(window=200).mean()
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Extract raw floats to prevent ValueError comparison errors
            price_close = float(latest['Close'])
            price_open = float(latest['Open'])
            price_low = float(latest['Low'])
            price_high = float(latest['High'])
            sma44_now = float(latest['SMA44'])
            sma44_prev = float(prev['SMA44'])
            sma200_now = float(latest['SMA200'])
            sma200_prev = float(prev['SMA200'])
            
            # STRATEGY LOGIC
            is_sma_rising = (sma44_now > sma44_prev) and (sma200_now > sma200_prev)
            is_green_candle = price_close > price_open
            is_at_support = price_low <= (sma44_now * 1.01) # Near 44 SMA
            
            if is_sma_rising and is_green_candle and is_at_support:
                # RISK MANAGEMENT MATH
                buy_above = round(price_high, 2)
                sl = round(price_low * 0.998, 2) # 0.2% buffer below low
                risk = buy_above - sl
                
                if risk > 0:
                    target1 = round(buy_above + (risk * 1), 2)
                    target2 = round(buy_above + (risk * 2), 2)
                    
                    bullish_stocks.append({
                        "Ticker": ticker.replace(".NS", ""),
                        "LTP": round(price_close, 2),
                        "Buy Above": buy_above,
                        "Stop Loss": sl,
                        "Target 1:1": target1,
                        "Target 1:2": target2,
                        "SMA44": round(sma44_now, 2)
                    })
        except:
            continue
            
    progress_bar.empty()
    return pd.DataFrame(bullish_stocks)

# --- UI INTERFACE ---
st.title("📈 5 PM Nifty 500 Scanner")
st.subheader("Strategy: 44 SMA Support + 200 SMA Bullish")

last_trade_date = get_last_trading_day().strftime('%Y-%m-%d')
st.info(f"Scanning data for: **{last_trade_date}** (Weekends auto-revert to Friday)")

if st.button('🚀 Start Market Scan'):
    with st.spinner('Analyzing 500 stocks... this takes ~2 minutes'):
        watchlist = get_nifty500_tickers()
        results = scan_stocks(watchlist)
        
        if not results.empty:
            st.success(f"Found {len(results)} Potential Trades!")
            st.dataframe(results, use_container_width=True)
            
            # Download functionality
            csv = results.to_csv(index=False).encode('utf-8')
            st.download_button("📩 Download Trade Plan CSV", csv, f"trades_{last_trade_date}.csv", "text/csv")
        else:
            st.warning("No stocks matched the 44 SMA support criteria today.")

st.markdown("---")
st.caption("Disclaimer: This tool is for educational purposes. Always consult a financial advisor before trading.")
