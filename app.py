from __future__ import annotations
import os
import math
import logging
import warnings
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Optional

warnings.filterwarnings("ignore")

# --- 1. SINGLETON CONFIG ---
class AppConfig:
    _inst: Optional[AppConfig] = None
    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
            cls._inst._init()
        return cls._inst

    def _init(self):
        self.sma_fast = 44
        self.sma_slow = 200
        self.rsi_period = 14
        self.fetch_workers = 15  # Optimized for speed
        self.history_days = 450

cfg = AppConfig()

# --- 2. THE UNIVERSE ---
NIFTY_200 = [
    'ABB.NS','ACC.NS','ADANIENSOL.NS','ADANIENT.NS','ADANIGREEN.NS','ADANIPORTS.NS',
    'ADANIPOWER.NS','ATGL.NS','AMBUJACEM.NS','APOLLOHOSP.NS','ASIANPAINT.NS','AUBANK.NS',
    'AUROPHARMA.NS','DMART.NS','AXISBANK.NS','BAJAJ-AUTO.NS','BAJFINANCE.NS','BAJAJFINSV.NS',
    'BAJAJHLDNG.NS','BALKRISIND.NS','BANDHANBNK.NS','BANKBARODA.NS','BANKINDIA.NS',
    'BERGEPAINT.NS','BEL.NS','BHARTIARTL.NS','BIOCON.NS','BOSCHLTD.NS','BPCL.NS',
    'BRITANNIA.NS','CANBK.NS','CHOLAFIN.NS','CIPLA.NS','COALINDIA.NS','COFORGE.NS',
    'COLPAL.NS','CONCOR.NS','CUMMINSIND.NS','DLF.NS','DABUR.NS','DALBHARAT.NS',
    'DEEPAKNTR.NS','DIVISLAB.NS','DIXON.NS','DRREDDY.NS','EICHERMOT.NS','ESCORTS.NS',
    'EXIDEIND.NS','FEDERALBNK.NS','GAIL.NS','GLAND.NS','GLENMARK.NS','GODREJCP.NS',
    'GODREJPROP.NS','GRASIM.NS','GUJGASLTD.NS','HAL.NS','HCLTECH.NS','HDFCBANK.NS',
    'HDFCLIFE.NS','HEROMOTOCO.NS','HINDALCO.NS','HINDCOPPER.NS','HINDPETRO.NS',
    'HINDUNILVR.NS','ICICIBANK.NS','ICICIGI.NS','ICICIPRULI.NS','IDFCFIRSTB.NS','ITC.NS',
    'INDIAHOTEL.NS','IOC.NS','IRCTC.NS','IRFC.NS','IGL.NS','INDUSTOWER.NS','INDUSINDBK.NS',
    'INFY.NS','IPCALAB.NS','JSWSTEEL.NS','JSL.NS','JUBLFOOD.NS','KOTAKBANK.NS','LT.NS',
    'LTIM.NS','LTTS.NS','LICHSGFIN.NS','LICI.NS','LUPIN.NS','MRF.NS','M&M.NS','M&MFIN.NS',
    'MARICO.NS','MARUTI.NS','MAXHEALTH.NS','MPHASIS.NS','NHPC.NS','NMDC.NS','NTPC.NS',
    'NESTLEIND.NS','OBEROIRLTY.NS','ONGC.NS','OIL.NS','PAYTM.NS','PIIND.NS','PFC.NS',
    'POLYCAB.NS','POWARGRID.NS','PRESTIGE.NS','RELIANCE.NS','RVNL.NS','RECLTD.NS',
    'SBICARD.NS','SBILIFE.NS','SRF.NS','SHREECEM.NS','SHRIRAMFIN.NS','SIEMENS.NS',
    'SONACOMS.NS','SBIN.NS','SAIL.NS','SUNPHARMA.NS','SUNTV.NS','SYNGENE.NS',
    'TATACOMM.NS','TATAELXSI.NS','TATACONSUM.NS','TATAMOTORS.NS','TATAPOWER.NS',
    'TATASTEEL.NS','TCS.NS','TECHM.NS','TITAN.NS','TORNTPHARM.NS','TRENT.NS','TIINDIA.NS',
    'UPL.NS','ULTRACEMCO.NS','UNITDSPR.NS','VBL.NS','VEDL.NS','VOLTAS.NS','WIPRO.NS',
    'YESBANK.NS','ZOMATO.NS','ZYDUSLIFE.NS'
]

# --- 3. UI STYLING ---
st.set_page_config(page_title="ArthaSutra Alpha", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #060c14; color: #e8f0f8; }
    .sig-card { background: #080f19; border: 1px solid #162030; border-radius: 8px; padding: 20px; margin-bottom: 15px; border-left: 5px solid #00d4aa; }
    .label { color: #7fa8c4; font-size: 10px; font-family: monospace; letter-spacing: 2px; }
    .value { font-size: 18px; font-weight: bold; color: #00d4aa; }
</style>
""", unsafe_allow_html=True)

# --- 4. ENGINE LOGIC ---
def process_stock(ticker, target_date):
    try:
        start_date = target_date - timedelta(days=cfg.history_days)
        df = yf.download(ticker, start=start_date, end=datetime.now(), auto_adjust=True, progress=False)
        if df.empty or len(df) < 200: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Vectorized Indicators
        df['SMA44'] = df['Close'].rolling(44).mean()
        df['SMA200'] = df['Close'].rolling(200).mean()
        
        # Logic: 44 SMA Support & Trend
        ts = pd.Timestamp(target_date)
        v_dates = df.index[df.index.date <= target_date]
        if v_dates.empty: return None
        t_ts = v_dates[-1]
        
        row = df.loc[t_ts]
        if row['Close'] > row['SMA44'] > row['SMA200'] and row['Close'] > row['Open']:
            risk = row['Close'] - row['Low']
            if risk <= 0 or (risk/row['Close']) > 0.07: return None
            
            return {
                "Ticker": ticker.replace(".NS", ""),
                "Entry": round(row['Close'], 2),
                "SL": round(row['Low'], 2),
                "T1": round(row['Close'] + risk, 2),
                "T2": round(row['Close'] + 2*risk, 2),
                "Date": t_ts.date()
            }
    except: return None
    return None

# --- 5. MAIN UI ---
def main():
    st.sidebar.title("◈ ARTHASUTRA V3")
    target_date = st.sidebar.date_input("SELECT AUDIT DATE", datetime.now().date() - timedelta(days=1))
    
    st.markdown("### 💹 NIFTY 200 | QUANTITATIVE ALPHA SCANNER")
    
    # SEBI Compliance Footer
    st.sidebar.warning("NOT SEBI REGISTERED: Research tool only.")

    if st.button("🚀 INITIATE SCAN", use_container_width=True):
        results = []
        prog = st.progress(0)
        
        with ThreadPoolExecutor(max_workers=cfg.fetch_workers) as executor:
            futures = {executor.submit(process_stock, t, target_date): t for t in NIFTY_200}
            for i, f in enumerate(as_completed(futures)):
                res = f.result()
                if res: results.append(res)
                prog.progress((i + 1) / len(NIFTY_200))
        
        prog.empty()

        if results:
            cols = st.columns(3)
            for idx, res in enumerate(results):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div class="sig-card">
                        <div class="label">TICKER</div>
                        <div class="value">{res['Ticker']}</div>
                        <hr style="border-color:#162030">
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                            <div><div class="label">ENTRY</div><div style="color:white">₹{res['Entry']}</div></div>
                            <div><div class="label">STOP</div><div style="color:#ff4d6d">₹{res['SL']}</div></div>
                            <div><div class="label">TARGET 1</div><div style="color:#f5c842">₹{res['T1']}</div></div>
                            <div><div class="label">TARGET 2</div><div style="color:#00d4aa">₹{res['T2']}</div></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.error("No setups found for this date.")

    # Mandatory Legal Disclosure
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 10px; color: #364f66; line-height:1.5; text-align:center;">
        <b>SEBI DISCLOSURE:</b> This application is for educational and research purposes. We are NOT SEBI registered advisors. 
        Trading involves risk of capital loss. Past performance does not guarantee future results.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
