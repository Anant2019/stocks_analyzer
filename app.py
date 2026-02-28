import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200 Live Signal Pro", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🏹 Nifty 200: Live Market Verdict")

# User aaj ki date select karega (default: Today)
target_date = st.date_input("Analysis Date", datetime.now())

def run_live_analysis():
    results = []
    progress_bar = st.progress(0)
    t_ts = pd.Timestamp(target_date)

    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=400), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201 or t_ts not in data.index: continue
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            
            day_data = data.loc[t_ts]
            close, open_p, low_p = float(day_data['Close']), float(day_data['Open']), float(day_data['Low'])
            sma44, sma200 = float(day_data['SMA_44']), float(day_data['SMA_200'])

            # Triple Bullish Logic
            if close > sma44 and sma44 > sma200 and close > open_p:
                future_df = data[data.index > t_ts]
                
                # Agar future data nahi hai (yani aaj ka signal hai), toh Status "LIVE" rahega
                if future_df.empty:
                    results.append({"Stock": ticker.replace(".NS",""), "Status": "🔵", "Result": "LIVE SIGNAL", "Entry": round(close, 2), "SL": round(low_p, 2)})
                    continue

                entry_p, sl = close, low_p
                risk = entry_p - sl
                t1, t2 = entry_p + risk, entry_p + (2 * risk)
                dot, outcome, t1_hit = "⏳", "Running", False
                
                for f_dt, f_row in future_df.iterrows():
                    h, l = float(f_row['High']), float(f_row['Low'])
                    if not t1_hit:
                        if l <= sl: dot, outcome = "🔴", "Loss"; break
                        if h >= t1: t1_hit, dot, outcome = True, "🟢", "T1 Hit"
                    else:
                        if h >= t2: dot, outcome = "🟢", "T2 Hit"; break
                        if l <= entry_p: dot, outcome = "🟡", "Break Even"; break
                
                results.append({"Stock": ticker.replace(".NS",""), "Status": dot, "Result": outcome, "Entry": round(entry_p, 2), "SL": round(sl, 2)})
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🔍 Start Live Analysis'):
    df_res = run_live_analysis()
    
    if not df_res.empty:
        total = len(df_res)
        success = len(df_res[df_res['Status'] == "🟢"])
        loss = len(df_res[df_res['Status'] == "🔴"])
        live = len(df_res[df_res['Status'] == "🔵"])
        
        # --- VERDICT LOGIC ---
        st.subheader("📢 Market Final Verdict")
        if total > 0:
            # Agar purane signals ka win rate 60% se upar hai
            win_rate = (success / (total - live)) * 100 if (total - live) > 0 else 0
            
            if live > 0 and (win_rate >= 60 or (total-live) == 0):
                st.success(f"✅ POSITIVE: {live} Naye signals mile hain aur pichla record solid hai. Buy entry le sakte hain!")
            elif win_rate < 40 and (total - live) > 0:
                st.error(f"❌ NEGATIVE: Pichle signals fail ho rahe hain. Aaj trade avoid karein!")
            else:
                st.warning("⚠️ NEUTRAL: Market confuse hai. Chote capital se trade karein.")

        # --- STATS ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Signals", total)
        c2.metric("Success", f"{success}")
        c3.metric("Loss", f"{loss}")
        c4.metric("New Live (Today)", f"{live}")

        st.divider()
        st.table(df_res)
    else:
        st.info("Aaj koi Triple Bullish signal nahi hai. Market side-ways ho sakta hai.")
