import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PERFORMANCE: CACHING & CONFIG ---
st.set_page_config(page_title="ArthaSutra", layout="wide", initial_sidebar_state="collapsed")

@st.cache_data(ttl=3600)  # Cache data for 1 hour to boost mobile speed
def fetch_data(ticker, start_date):
    try:
        data = yf.download(ticker, start=start_date, end=datetime.now(), auto_adjust=True, progress=False)
        return data
    except:
        return None

# --- 2. MOBILE-FIRST CSS (NO SCROLLING) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #00FFA3 !important; }
    .stock-card {
        background-color: #1A1C23;
        border: 1px solid #333;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .traffic-green { color: #00FFA3; font-weight: bold; }
    .traffic-red { color: #FF4B4B; font-weight: bold; }
    .stButton button { width: 100%; border-radius: 12px; height: 3rem; background-color: #262730; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. REFINED LEGAL DISCLOSURE ---
with st.expander("⚖️ LEGAL DISCLOSURE (Non-SEBI)", expanded=False):
    st.caption("We are NOT SEBI REGISTERED. All calculations are for educational swing-trading practice. Risk capital only.")

# --- 4. TOP-LEVEL SETTINGS (NO SIDEBAR) ---
st.title("💹 ArthaSutra")
st.markdown("### `Discipline • Prosperity • Consistency` ")

with st.expander("🛠️ Strategy & Risk Settings", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        risk_per_trade = st.number_input("Max Loss per Trade (₹)", value=1000, step=500)
    with col2:
        target_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=1))
    run_btn = st.button('🚀 SCAN MARKET')

# --- 5. SWING ENGINE ---
def run_swing_audit(risk_amt, t_date):
    # Shortened list for demo speed; can be expanded to NIFTY_200
    TICKERS = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'BHARTIARTL.NS', 'SBIN.NS', 'ITC.NS'] 
    
    results = []
    start_lookback = t_date - timedelta(days=400)
    
    for ticker in TICKERS:
        data = fetch_data(ticker, start_lookback)
        if data is None or len(data) < 200: continue
        
        # Fixing MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        # Signal Generation
        data['SMA_44'] = data['Close'].rolling(window=44).mean()
        data['SMA_200'] = data['Close'].rolling(window=200).mean()
        
        # Filter for the specific date
        valid_days = data.index[data.index.date <= t_date]
        if valid_days.empty: continue
        d = data.loc[valid_days[-1]]
        
        # Swing Logic: Structural Strength
        is_bullish = d['Close'] > d['SMA_44'] > d['SMA_200']
        
        if is_bullish:
            entry = d['Close']
            stop_loss = d['Low']
            risk_points = entry - stop_loss
            if risk_points <= 0: continue
            
            qty = int(risk_amt / risk_points)
            target = entry + (risk_points * 2)
            rrr = 2.0  # Simplified for strategy audit
            
            results.append({
                "Symbol": ticker.replace(".NS",""),
                "Price": round(entry, 2),
                "SL": round(stop_loss, 2),
                "Target": round(target, 2),
                "Qty": qty,
                "RRR": rrr,
                "Reason": "Price structure confirmed above 44/200 SMA confluence."
            })
    return results

# --- 6. MOBILE CARD DISPLAY ---
if run_btn:
    cards = run_swing_audit(risk_per_trade, target_date)
    
    if cards:
        st.success(f"Found {len(cards)} Swing Setups")
        for c in cards:
            # The "Card" UI
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.5rem; font-weight: bold;">{c['Symbol']}</span>
                    <span class="traffic-green">RRR {c['RRR']}:1</span>
                </div>
                <hr style="margin: 10px 0; border-color: #333;">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <p style="margin:0; color: #888; font-size: 0.8rem;">ENTRY</p>
                        <p style="margin:0; font-size: 1.1rem; font-weight: bold;">₹{c['Price']}</p>
                    </div>
                    <div>
                        <p style="margin:0; color: #888; font-size: 0.8rem;">STOP LOSS</p>
                        <p style="margin:0; font-size: 1.1rem; font-weight: bold; color: #FF7E7E;">₹{c['SL']}</p>
                    </div>
                    <div>
                        <p style="margin:0; color: #888; font-size: 0.8rem;">TARGET</p>
                        <p style="margin:0; font-size: 1.1rem; font-weight: bold; color: #00FFA3;">₹{c['Target']}</p>
                    </div>
                </div>
                <div style="margin-top: 15px; padding: 10px; background: #262730; border-radius: 8px;">
                    <p style="margin:0; color: #00FFA3; font-size: 0.9rem;"><b>Position Size: Buy {c['Qty']} Shares</b></p>
                    <p style="margin:0; color: #AAA; font-size: 0.8rem; margin-top: 5px;">{c['Reason']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action Buttons for Mobile
            col_a, col_b = st.columns(2)
            with col_a:
                st.link_button(f"📈 Chart", f"https://www.tradingview.com/chart/?symbol=NSE:{c['Symbol']}")
            with col_b:
                st.button(f"🔔 Alert", key=f"alert_{c['Symbol']}")
    else:
        st.warning("No high-probability swing setups found for this date.")

st.divider()
st.caption("ArthaSutra v6.5 • Optimized for 4G/LTE Mobile Access")
