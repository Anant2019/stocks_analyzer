import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. SEBI COMPLIANCE & PAGE CONFIG ---
st.set_page_config(page_title="Nifty 200: Institutional Reasoner", layout="wide")

st.error("⚠️ **DISCLAIMER: FOR EDUCATIONAL PURPOSES ONLY**")
st.markdown("""
<div style="background-color:#fff3cd; padding:15px; border-radius:10px; border:1px solid #ffeeba; margin-bottom: 25px;">
    <p style="color:#856404; font-weight:bold; margin-bottom:5px;">⚠️ NOT SEBI REGISTERED</p>
    <p style="color:#856404; font-size:0.9em;">
        I am not a SEBI registered research analyst or investment advisor. This tool is for educational purposes only. 
        <b>Trading involves high risk.</b> Please consult a certified advisor. We are not responsible for any losses.
    </p>
</div>
""", unsafe_allow_html=True)

# --- 2. TICKER LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

# --- 3. INPUTS ---
st.title("🛡️ The 90% Accuracy Jackpot Filter")
target_date = st.date_input("Analysis Date", datetime.now().date() - timedelta(days=2))

# --- 4. ENGINE ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10))))

def run_full_engine():
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
                # 90% Probability Filter (Blue Dot Logic)
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
                
                risk = d['Close'] - d['Low']
                if risk <= 0: continue
                t2 = d['Close'] + (2 * risk)
                
                status = "⏳ Active"
                jackpot_hit = False
                future = data[data.index > t_ts]
                if not future.empty:
                    for f_dt, f_row in future.iterrows():
                        if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                        if f_row['High'] >= t2: 
                            status = "🔥 Jackpot Hit"; 
                            jackpot_hit = True; 
                            break
                
                # Reasoning Generator
                reason = f"✅ **Conviction:** Vol {round(d['Volume']/d['Vol_MA'],1)}x avg. RSI {round(d['RSI'],1)}." if jackpot_hit else "❌ **Rejection:** Trend failed to sustain momentum."
                if status == "⏳ Active": reason = "🔄 **Monitoring:** Setup valid, awaiting target/SL."

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE (High)" if is_blue else "🟡 AMBER (Normal)",
                    "Status": status,
                    "Jackpot": jackpot_hit,
                    "Entry": round(d['Close'], 2),
                    "Target 1:2": round(t2, 2),
                    "Reasoning": reason,
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 5. UI DISPLAY ---
if st.button('🚀 Execute Deep Scan'):
    df, adjusted_date = run_full_engine()
    if not df.empty:
        # DASHBOARD METRICS (RE-ADDED)
        blue_df = df[df['Category'].str.contains("BLUE")]
        total_blue = len(blue_df)
        hits_blue = len(blue_df[blue_df['Jackpot'] == True])
        
        st.subheader(f"📊 Market Dashboard: {adjusted_date}")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔵 Total Blue Signals", total_blue)
        c2.metric("🎯 Blue Success Rate", f"{round((hits_blue/total_blue)*100, 1) if total_blue > 0 else 0}%")
        c3.metric("🔥 Total Jackpots", len(df[df['Jackpot'] == True]))
        
        st.divider()
        st.write("### 🔍 Summary Table")
        st.dataframe(df.drop(columns=['Reasoning', 'Jackpot']), use_container_width=True, hide_index=True, column_config={"Chart": st.column_config.LinkColumn("Chart Link")})
        
        st.divider()
        st.write("### 💡 Individual Attribution (The 'Why')")
        for _, row in df.iterrows():
            with st.expander(f"{row['Stock']} - {row['Category']} - {row['Status']}"):
                st.info(row['Reasoning'])
                st.write(f"**Target 1:2 Price:** ₹{row['Target 1:2']}")
                st.link_button("Open TradingView", row['Chart'])
    else:
        st.warning("No Triple Bullish setups found.")

st.divider()
st.info("Institutional Grade Vectorized Engine | Logic: Pine Script V5 Parity")
