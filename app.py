import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. INSTITUTIONAL PAGE CONFIG ---
st.set_page_config(page_title="ArthaSutra | Strategy Auditor", layout="wide", page_icon="💹")

# --- 2. MANDATORY SEBI DISCLAIMER (RETAINED) ---
st.error("⚠️ **LEGAL COMPLIANCE & DISCLOSURE**")
st.markdown("""
<div style="background-color:#fff3cd; padding:18px; border-radius:12px; border:2px solid #ffc107; margin-bottom: 25px;">
    <h4 style="color:#856404; margin-top:0;">⚠️ NOT SEBI REGISTERED</h4>
    <p style="color:#856404; font-size:1.0em; line-height:1.5;">
        <b>ArthaSutra</b> is an automated analytical tool for educational research. We are <b>NOT SEBI registered</b> investment advisors or research analysts. 
        The 'Blue' conviction signals and 'Jackpot' hits are based on historical backtesting and mathematical algorithms. 
        <br><br>
        Stock market investments are subject to market risks. Please consult a SEBI registered financial advisor before making any investment decisions. 
        <b>We are not liable for any financial gains or losses incurred using this tool.</b>
    </p>
</div>
""", unsafe_allow_html=True)

# --- 3. NIFTY 200 TICKER LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

# --- 4. CALCULATION ENGINE ---
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
            
            # Holiday Check
            valid_dates = data.index[data.index.date <= target_date]
            if valid_dates.empty: continue
            t_ts = valid_dates[-1]
            actual_date = t_ts.date()

            # Technicals
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['Vol_MA'] = data['Volume'].rolling(window=20).mean()
            data['RSI'] = calculate_rsi(data['Close'])

            d = data.loc[t_ts]
            # Triple Bullish Strategy
            if d['Close'] > d['SMA_44'] and d['SMA_44'] > d['SMA_200'] and d['Close'] > d['Open']:
                # Conviction Filter
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
                
                v_ratio = d['Volume'] / d['Vol_MA']
                # Reasoning Generator
                if status == "🟢 Jackpot Hit":
                    analysis = f"🏆 **Why it won?**\nStrong institutional buying confirmed by {v_ratio:.1f}x average volume. The bullish trend was well-sustained above the safety level (SL) of ₹{round(d['Low'],2)}."
                elif status == "🔴 SL Hit":
                    analysis = f"📉 **Why it failed?**\nBull Trap detected. Despite the breakout, follow-through volume was missing, and sellers regained control below the signal day's low."
                else:
                    analysis = f"⏳ **In Progress:**\nThe setup remains technically valid. Target (1:2) is set at ₹{round(t2,2)} while the safety level (SL) is ₹{round(d['Low'],2)}."

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE (High Conviction)" if is_blue else "🟡 AMBER (Standard)",
                    "Status": status,
                    "Jackpot": jackpot_hit,
                    "Entry": round(d['Close'], 2),
                    "Target 1:2": round(t2, 2),
                    "Deep Analysis": analysis,
                    "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results), actual_date

# --- 5. UI DISPLAY ---
st.title("💹 ArthaSutra: Institutional Strategy Auditor")
st.markdown("#### *Precision. Discipline. Prosperity.*")

col_d, col_b = st.columns([2, 1])
with col_d:
    selected_date = st.date_input("Audit Date Selection", datetime.now().date() - timedelta(days=2))

if st.button('🚀 Start Strategy Audit', use_container_width=True):
    df, adjusted_date = run_arthasutra_engine(selected_date)
    
    if not df.empty:
        blue_df = df[df['Category'].str.contains("BLUE")]
        total_blue = len(blue_df)
        hits_blue = len(blue_df[blue_df['Jackpot'] == True])
        
        st.subheader(f"📊 Audit Performance: {adjusted_date}")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔵 High Conviction Signals", total_blue)
        c2.metric("🎯 Blue Success Rate", f"{round((hits_blue/total_blue)*100, 1) if total_blue > 0 else 0}%")
        c3.metric("🔥 Total Jackpots Hit", len(df[df['Jackpot'] == True]))
        
        # Download Report
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📂 Download Comprehensive Report (CSV)", data=csv, file_name=f"ArthaSutra_Audit_{adjusted_date}.csv", mime='text/csv')

        st.divider()
        st.write("### 🔍 Live Signal Tracker")
        st.dataframe(df.drop(columns=['Deep Analysis', 'Jackpot']), use_container_width=True, hide_index=True, 
                     column_config={"Chart": st.column_config.LinkColumn("Deep Link")})
        
        st.divider()
        st.write("### 💡 Strategic Attribution (Beginner-Friendly Why)")
        for _, row in df.iterrows():
            with st.expander(f"Analysis: {row['Stock']} | {row['Status']}"):
                st.markdown(row['Deep Analysis'])
                st.link_button(f"Analyze {row['Stock']} on TradingView", row['Chart'])
    else:
        st.warning("No Triple Bullish setups detected. Markets might be in a consolidation phase.")

st.divider()
st.info("ArthaSutra Framework v3.0 | SMA 44-200 Vectorized Backtest Engine")
