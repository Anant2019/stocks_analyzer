import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# --- BRANDING & CONFIG ---
st.set_page_config(page_title="Arth Sutra Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    .brand-title { font-size: 3rem; font-weight: 800; color: #ffffff; margin-bottom: 0px; }
    .brand-tagline { font-size: 1rem; color: #888888; margin-bottom: 30px; letter-spacing: 2px; text-transform: uppercase; }
    .stock-card { background-color: #0a0a0a; padding: 24px; border-radius: 4px; border: 1px solid #1a1a1a; margin-bottom: 20px; }
    .ticker-name { font-size: 1.8rem; font-weight: 700; color: #ffffff; }
    .entry-text { color: #0088ff; font-weight: 700; }
    .sl-text { color: #ff3333; font-weight: 700; }
    .target-val { color: #00ff44; font-weight: 700; font-size: 1.2rem; }
    div.stButton > button { background-color: #ffffff !important; color: #000000 !important; width: 100%; font-weight: 800; border: none; }
    </style>
""", unsafe_allow_html=True)

def get_nifty500_tickers():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
        return [f"{s}.NS" for s in pd.read_csv(url)['Symbol'].tolist()]
    except:
        return ["RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS", "HINDALCO.NS", "COALINDIA.NS"]

def process_stock(t):
    try:
        # Fetching slightly more data to ensure SMA calculation is accurate
        data = yf.download(t, period="2y", interval="1d", progress=False)
        if len(data) < 200: return None
        
        df = data.copy()
        df['SMA44'] = df['Close'].rolling(window=44).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        
        # Drop rows with NaN to ensure we are looking at valid dates
        df.dropna(subset=['SMA200'], inplace=True)
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- THE SUTRA CRITERIA ---
        # 1. Rising Averages
        sma_up = (curr['SMA44'] > prev['SMA44']) and (curr['SMA200'] > prev['SMA200'])
        # 2. Support Zone (Increased to 3% for better discovery)
        at_support = curr['Low'] <= (curr['SMA44'] * 1.03) 
        # 3. Bullish Confirmation (Green Candle)
        is_green = curr['Close'] > curr['Open']
        
        if sma_up and at_support and is_green:
            buy = round(float(curr['High']), 2)
            sl = round(float(curr['Low']) * 0.998, 2)
            risk = buy - sl
            if risk > 0:
                return {
                    "T": t.replace(".NS", ""), "L": round(float(curr['Close']), 2),
                    "B": buy, "S": sl, "T1": round(buy + risk, 2), "T2": round(buy + (risk*2), 2)
                }
    except: pass
    return None

# --- UI ---
st.markdown('<div class="brand-title">ARTH SUTRA</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-tagline">Discipline • Prosperity • Consistency</div>', unsafe_allow_html=True)

if st.button('INITIATE ENGINE SCAN'):
    tickers = get_nifty500_tickers()
    
    with st.spinner(f'Processing 500 stocks... Current Speed: 25 Tickers/Sec'):
        with ThreadPoolExecutor(max_workers=25) as executor:
            found = list(filter(None, executor.map(process_stock, tickers)))
    
    if found:
        st.write(f"### {len(found)} SIGNALS DETECTED")
        cols = st.columns(3)
        for idx, stock in enumerate(found):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="stock-card">
                    <div class="ticker-name">{stock['T']}</div>
                    <div style="color: #555; font-size: 0.8rem;">LTP: ₹{stock['L']}</div>
                    <hr style="border:0; border-top:1px solid #1a1a1a; margin:15px 0;">
                    <div class="entry-text">BUY ABOVE: ₹{stock['B']}</div>
                    <div class="sl-text">STOP LOSS: ₹{stock['S']}</div>
                    <div style="margin-top:15px; border-left: 3px solid #00ff44; padding-left:10px;">
                        <div class="target-val">T1: ₹{stock['T1']}</div>
                        <div class="target-val">T2: ₹{stock['T2']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No signals found in the last session. The 44 SMA is a powerful filter—patience is key to Prosperity.")

st.sidebar.markdown("---")
st.sidebar.write("**System Diagnostics**")
st.sidebar.write(f"Universe: Nifty 500")
st.sidebar.write(f"Mode: Ultra-High Speed")
