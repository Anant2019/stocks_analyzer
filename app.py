import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. SEBI COMPLIANCE & PAGE CONFIG ---
st.set_page_config(page_title="Nifty 200: Strategy Auditor", layout="wide")

st.error("⚠️ **DISCLAIMER: FOR EDUCATIONAL PURPOSES ONLY**")
st.markdown("""
<div style="background-color:#fff3cd; padding:15px; border-radius:10px; border:1px solid #ffeeba; margin-bottom: 25px;">
    <p style="color:#856404; font-weight:bold; margin-bottom:5px;">⚠️ NOT SEBI REGISTERED</p>
    <p style="color:#856404; font-size:0.9em;">
        I am not a SEBI registered research analyst. This tool is for learning how the 'Triple Bullish' strategy works. 
        <b>Stock market investments are subject to market risks.</b> Never trade with money you cannot afford to lose.
    </p>
</div>
""", unsafe_allow_html=True)

# --- 2. TICKER LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

# --- 3. INPUTS ---
st.title("🛡️ Beginner-Friendly Jackpot Auditor")
target_date = st.date_input("Select Analysis Date", datetime.now().date() - timedelta(days=2))

# --- 4. CALCULATION ENGINE ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / (loss + 1e-10))))

def run_beginner_engine():
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
            # Triple Bullish Check
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                
                is_blue = d['RSI'] > 65 and d['Volume'] > d['Vol_MA'] and (d['Close'] > d['SMA_200'] * 1.05)
                risk = d['Close'] - d['Low']
                if risk <= 0: continue
                t2 = d['Close'] + (2 * risk)
                
                status = "⏳ Running"
                jackpot_hit = False
                future = data[data.index > t_ts]
                
                if not future.empty:
                    for f_dt, f_row in future.iterrows():
                        if f_row['Low'] <= d['Low']: status = "🔴 SL Hit"; break
                        if f_row['High'] >= t2: status = "🟢 Jackpot Hit"; jackpot_hit = True; break
                
                # --- BEGINNER FRIENDLY ANALYSIS ---
                v_ratio = d['Volume'] / d['Vol_MA']
                setup_desc = f"Stock is trending above both 44 and 200 day averages. "
                
                if status == "🟢 Jackpot Hit":
                    analysis = f"🏆 **Why it won?**\n\n1. **High Power:** Volume was {v_ratio:.1f}x higher than normal—meaning big players (Institutions) were buying.\n2. **Strong Trend:** The stock stayed above its safety level (Low of the day) and moved fast toward the target."
                elif status == "🔴 SL Hit":
                    analysis = f"📉 **Why it failed?**\n\n1. **Bull Trap:** Even though the setup looked good, sellers became stronger than buyers at the top.\n2. **Weak Follow-through:** There wasn't enough 'new money' to push the price higher, so it fell back to hit the Stop Loss."
                else:
                    analysis = f"⏳ **Current Situation:**\n\n- The setup is solid. We are waiting to see if buyers can keep the price above ₹{round(d['Low'], 2)}. If it stays above this, the target of ₹{round(t2, 2)} is possible."

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE (High Prob)" if is_blue else "🟡 AMBER (Normal)",
                    "Status": status,
                    "Jackpot": jackpot_hit,
                    "Entry": round(d['Close'], 2),
                    "Target (1:2)": round(t2, 2),
                    "Beginner_Analysis": analysis,
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 5. UI DISPLAY ---
if st.button('🚀 Start Deep Scan'):
    df, adjusted_date = run_beginner_engine()
    if not df.empty:
        # DASHBOARD METRICS
        blue_df = df[df['Category'].str.contains("BLUE")]
        total_blue = len(blue_df)
        hits_blue = len(blue_df[blue_df['Jackpot'] == True])
        
        st.subheader(f"📊 Market Summary: {adjusted_date}")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔵 High Conviction (Blue)", total_blue)
        c2.metric("🎯 Blue Success Rate", f"{round((hits_blue/total_blue)*100, 1) if total_blue > 0 else 0}%")
        c3.metric("🔥 Total Jackpots", len(df[df['Jackpot'] == True]))
        
        st.divider()
        st.write("### 🔍 Trade List")
        st.dataframe(df.drop(columns=['Beginner_Analysis', 'Jackpot']), use_container_width=True, hide_index=True, 
                     column_config={"Chart": st.column_config.LinkColumn("Chart Link")})
        
        st.divider()
        st.write("### 💡 Simple Analysis (Learn why trades move)")
        for _, row in df.iterrows():
            with st.expander(f"Analysis for {row['Stock']} ({row['Status']})"):
                st.markdown(row['Beginner_Analysis'])
                st.write(f"---")
                st.write(f"**Safety Level (SL):** ₹{row['Entry'] - (row['Target (1:2)'] - row['Entry'])/2}")
                st.link_button(f"See {row['Stock']} Chart", row['Chart'])
    else:
        st.warning("No Triple Bullish setups found. Markets might be sideways.")

st.divider()
st.info("Logic: Swing Triple Bullish 44-200. Built for clarity and accuracy.")
