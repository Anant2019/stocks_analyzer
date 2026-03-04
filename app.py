import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Strategy Auditor", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="💹"
)

# --- 2. DARK THEME & ALIGNMENT CSS ---
st.markdown("""
    <style>
    /* Dark Background & Text Consistency */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* Soften the Red Disclaimer */
    .stError {
        background-color: rgba(255, 75, 75, 0.1) !important;
        color: #FF7E7E !important;
        border: 1px solid rgba(255, 75, 75, 0.2) !important;
        border-radius: 10px;
    }

    /* Metric Card Styling */
    [data-testid="stMetricValue"] { 
        font-size: 2rem !important; 
        font-weight: 800; 
        color: #00FFA3 !important; /* Emerald Green */
    }
    
    /* Button Professional Alignment */
    .stButton button, .stDownloadButton button {
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-weight: 700;
        background-color: #262730;
        color: white;
        border: 1px solid #4B4B4B;
        transition: 0.3s;
    }
    
    .stButton button:hover {
        border-color: #00FFA3;
        color: #00FFA3;
    }

    /* Fixed alignment for Desktop */
    @media (min-width: 800px) {
        .stButton button, .stDownloadButton button {
            max-width: 300px;
            display: block;
            margin: 0 auto;
        }
        .centered-col {
            display: flex;
            justify-content: center;
        }
    }

    /* Expander Styling */
    .stExpander {
        background-color: #1A1C23;
        border: 1px solid #333;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MANDATORY SEBI DISCLAIMER (RETAINED & SOFTENED) ---
st.error("🔒 **REGULATORY DISCLOSURE**")
with st.expander("📝 View SEBI Compliance & Risk Terms", expanded=True):
    st.markdown("""
    <div style="background-color: rgba(255, 193, 7, 0.05); padding:20px; border-radius:12px; border:1px solid rgba(255, 193, 7, 0.3);">
        <h4 style="color:#FFC107; margin-top:0;">⚠️ NOT SEBI REGISTERED</h4>
        <p style="color:#CCCCCC; font-size:0.95em; line-height:1.6;">
            <b>ArthaSutra</b> is an grade A research algorithm for educational use. 
            We are <b>NOT SEBI registered</b> investment advisors. Our 'Blue' and 'Amber' signals 
            are mathematical derivations of historical trends.
            <br><br>
            <b>Capital Protection:</b> Trading involves market risks. Always use strict stop-losses. 
            <b>We are not responsible for any financial losses.</b>
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. TICKER LIST (INTACT) ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']

# --- 5. ENGINE CORE (INTACT) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10))))

def run_arthasutra_engine(target_date):
    results = []
    actual_date = None
    progress_bar = st.progress(0)
    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=410), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201: continue
            if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
            valid_dates = data.index[data.index.date <= target_date]
            if valid_dates.empty: continue
            t_ts = valid_dates[-1]
            actual_date = t_ts.date()
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
            data['RSI'] = calculate_rsi(data['Close'])
            d = data.loc[t_ts]
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
                risk = d['Close'] - d['Low']
                if risk <= 0: continue
                t2 = d['Close'] + (2 * risk)
                status, jackpot_hit = "⏳ Running", False
                future = data[data.index > t_ts]
                if not future.empty:
                    for f_dt, f_row in future.iterrows():
                        if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                        if f_row['High'] >= t2: status = "🟢 Jackpot Hit"; jackpot_hit = True; break
                
                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status, "Jackpot": jackpot_hit, "Entry": round(d['Close'], 2),
                    "Target": round(t2, 2), "RSI": round(d['RSI'], 1),
                    "Analysis": f"🏆 **Success:** High Institutional Volume detected. Support at ₹{round(d['Low'],2)} held." if jackpot_hit else f"📉 **Failure:** Market Volatility hit the Safety Level below ₹{round(d['Low'],2)}.",
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 6. DARK TERMINAL UI ---
st.title("💹 ArthaSutra")
st.caption("• Precision. Discipline. Prosperity.")

# Centered Inputs
_, col_input, _ = st.columns([1, 1.5, 1])
with col_input:
    selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=2))
    st.write("") # Spacer
    run_btn = st.button('🚀 Execute Analysis', use_container_width=True)

if run_btn:
    df, adjusted_date = run_arthasutra_engine(selected_date)
    if not df.empty:
        blue_df = df[df['Category'].str.contains("BLUE")]
        hits_blue = len(blue_df[blue_df['Jackpot'] == True])
        
        st.write(f"### 📊 Report for {adjusted_date}")
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("🔵 High Conviction", len(blue_df))
        m_col2.metric("🎯 Accuracy", f"{round((hits_blue/len(blue_df))*100, 1) if len(blue_df) > 0 else 0}%")
        m_col3.metric("🔥 Total Jackpots", len(df[df['Jackpot'] == True]))
        
        # Centered Download Button
        _, col_dl, _ = st.columns([1, 1, 1])
        with col_dl:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📂 Download Audit CSV", data=csv, file_name=f"ArthaSutra_{adjusted_date}.csv", mime='text/csv')

        st.divider()
        st.write("### 🔍 Live Signals Tracker")
        st.dataframe(df.drop(columns=['Analysis', 'Jackpot']), use_container_width=True, hide_index=True)
        
        st.divider()
        st.write("### 💡 Strategy Attribution (The 'Why')")
        for _, row in df.iterrows():
            with st.expander(f"{row['Stock']} | {row['Category']} | {row['Status']}"):
                st.markdown(row['Analysis'])
                st.write(f"**RSI:** {row['RSI']} | **Entry:** ₹{row['Entry']} | **Target:** ₹{row['Target']}")
                st.link_button(f"View Chart", row['Chart'], use_container_width=True)
    else:
        st.warning("No Triple Bullish setups found.")

st.divider()
st.caption("ArthaSutra v4.5 • Powered by SMA 44-200 Vector Engine")
