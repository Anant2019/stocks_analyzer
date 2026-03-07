import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# --- BRANDING & CONFIG ---
st.set_page_config(page_title="Arth Sutra Pro", layout="wide")

# --- ULTRA-DARK TERMINAL CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    
    /* Branding */
    .brand-title { font-size: 3rem; font-weight: 800; color: #ffffff; margin-bottom: 0px; }
    .brand-tagline { font-size: 1rem; color: #888888; margin-bottom: 30px; letter-spacing: 2px; text-transform: uppercase; }
    
    /* Card Design */
    .stock-card {
        background-color: #0a0a0a;
        padding: 24px;
        border-radius: 8px;
        border: 1px solid #1a1a1a;
        margin-bottom: 20px;
    }
    
    /* Elements */
    .ticker-name { font-size: 1.8rem; font-weight: 700; color: #ffffff; }
    .metric-label { color: #555555; font-size: 0.8rem; text-transform: uppercase; }
    .price-val { font-family: monospace; font-size: 1.2rem; color: #bbbbbb; }
    
    .entry-text { color: #0088ff; font-weight: 700; font-size: 1.1rem; }
    .sl-text { color: #ff3333; font-weight: 700; font-size: 1.1rem; }
    
    .target-container {
        border-left: 3px solid #00ff44;
        padding-left: 15px;
        margin-top: 15px;
    }
    .target-val { color: #00ff44; font-weight: 700; font-size: 1.2rem; }

    /* Button */
    div.stButton > button {
        background-color: #ffffff !important;
        color: #000000 !important;
        width: 100% !important;
        border-radius: 4px !important;
        font-weight: 800 !important;
        height: 3em !important;
    }
    
    /* Progress Bar Color */
    .stProgress > div > div > div > div { background-color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# --- LOGIC ---
def get_nifty500_tickers():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        df = pd.read_csv(url)
        return [f"{s}.NS" for s in df['Symbol'].tolist()]
    except:
        return ["RELIANCE.NS", "TCS.NS", "TATAMOTORS.NS"]

def scan_market(tickers):
    results = []
    progress_text = st.empty()
    bar = st.progress(0)
    
    for i, t in enumerate(tickers):
        try:
            progress_text.text(f"Scanning {i+1}/500: {t}")
            bar.progress((i + 1) / len(tickers))
            
            # Fetching 1 year of daily data
            df = yf.download(t, period="1y", interval="1d", progress=False)
            if len(df) < 200: continue
            
            df['SMA44'] = df['Close'].rolling(window=44).mean()
            df['SMA200'] = df['Close'].rolling(window=200).mean()
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # THE CORE SUTRA (LOGIC)
            is_rising = (curr['SMA44'] > prev['SMA44']) and (curr['SMA200'] > prev['SMA200'])
            is_support = curr['Low'] <= (curr['SMA44'] * 1.01)
            is_green = curr['Close'] > curr['Open']
            
            if is_rising and is_support and is_green:
                buy = round(float(curr['High']), 2)
                sl = round(float(curr['Low']) * 0.998, 2)
                risk = buy - sl
                if risk > 0:
                    results.append({
                        "T": t.replace(".NS", ""), "L": round(float(curr['Close']), 2),
                        "B": buy, "S": sl, "T1": round(buy + risk, 2), "T2": round(buy + (risk*2), 2)
                    })
        except: continue
    
    bar.empty()
    progress_text.empty()
    return results

# --- APP LAYOUT ---
st.markdown('<div class="brand-title">ARTH SUTRA</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-tagline">Discipline • Prosperity • Consistency</div>', unsafe_allow_html=True)

if st.button('INITIATE SYSTEM SCAN'):
    found = scan_market(get_nifty500_tickers())
    
    if found:
        st.write(f"### {len(found)} SIGNALS DETECTED")
        cols = st.columns(3)
        for idx, stock in enumerate(found):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="stock-card">
                    <div class="ticker-name">{stock['T']}</div>
                    <div class="metric-label">Last Traded Price</div>
                    <div class="price-val">₹{stock['L']}</div>
                    <hr style="border:0; border-top:1px solid #1a1a1a; margin:15px 0;">
                    <div class="entry-text">BUY ABOVE: ₹{stock['B']}</div>
                    <div class="sl-text">STOP LOSS: ₹{stock['S']}</div>
                    <div class="target-container">
                        <div class="metric-label">Targets (1:1 & 1:2)</div>
                        <div class="target-val">T1: ₹{stock['T1']}</div>
                        <div class="target-val">T2: ₹{stock['T2']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("System Online. No signals meeting the criteria were found in the Nifty 500.")

st.sidebar.markdown("---")
st.sidebar.write(f"**Market Status:** Closed (Weekend)")
st.sidebar.write(f"**Last Sync:** {datetime.now().strftime('%H:%M:%S')}")
