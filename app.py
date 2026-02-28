import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200: 90% Accuracy Tracker", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🛡️ The 90% Accuracy Jackpot Filter")

# --- DATE LOGIC ---
target_date = st.date_input("Backtest Date", datetime(2025, 12, 12))
if target_date.weekday() == 5: target_date -= timedelta(days=1)
if target_date.weekday() == 6: target_date -= timedelta(days=2)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def run_high_accuracy_backtest():
    results = []
    t_ts = pd.Timestamp(target_date)
    progress_bar = st.progress(0)

    for i, ticker in enumerate(NIFTY_200):
        try:
            # Note: start date 450 days back for accurate SMA 200
            data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201 or t_ts not in data.index: continue
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['RSI'] = calculate_rsi(data['Close'])
            data['Vol_Avg'] = data['Volume'].rolling(window=5).mean()
            
            day_data = data.loc[t_ts]
            close, open_p, low_p = float(day_data['Close']), float(day_data['Open']), float(day_data['Low'])
            sma44, sma200, rsi = float(day_data['SMA_44']), float(day_data['SMA_200']), float(day_data['RSI'])
            vol, vol_avg = float(day_data['Volume']), float(day_data['Vol_Avg'])

            if close > sma44 and sma44 > sma200 and close > open_p:
                # 90% PROBABILITY FILTER (Blue Dot)
                is_blue = rsi > 65 and vol > vol_avg and (close > sma200 * 1.05)
                
                risk = close - low_p
                t2 = close + (2 * risk)
                future_df = data[data.index > t_ts]
                
                status, jackpot_hit, analysis = "⏳ Running", False, "Price is above key SMAs. Momentum is building."
                
                if not future_df.empty:
                    for f_dt, f_row in future_df.iterrows():
                        if f_row['Low'] <= low_p: 
                            status = "🔴 SL Hit"
                            analysis = f"Support level broken. Even with RSI at {round(rsi,1)}, selling pressure was too high."
                            break
                        if f_row['High'] >= t2: 
                            status = "🔥 Jackpot Hit (1:2)"
                            jackpot_hit = True
                            analysis = f"Momentum Win! RSI was strong at {round(rsi,1)} and Volume surge was {round(vol/vol_avg,1)}x. Target reached comfortably."
                            break

                results.append({
                    "Stock": ticker.replace(".NS",""),
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status,
                    "Jackpot": jackpot_hit,
                    "Entry": round(close, 2),
                    "Target_2": round(t2, 2),
                    "RSI": round(rsi, 1),
                    "Vol_Ratio": round(vol/vol_avg, 2),
                    "Analysis": analysis
                })
        except: continue
        progress_bar.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Run Analysis'):
    df = run_high_accuracy_backtest()
    if not df.empty:
        blue_df = df[df['Category'].str.contains("BLUE")]
        
        # --- DASHBOARD ---
        st.subheader(f"📊 Market Summary: {target_date}")
        c1, c2, c3 = st.columns(3)
        c1.metric("🔵 Blue Signals", len(blue_df))
        c2.metric("🔥 Blue Jackpots", len(blue_df[blue_df['Jackpot'] == True]))
        accuracy = (len(blue_df[blue_df['Jackpot'] == True]) / len(blue_df) * 100) if len(blue_df) > 0 else 0
        c3.metric("🎯 Blue Accuracy", f"{round(accuracy, 1)}%")
        
        st.divider()
        
        # --- NEW INTERACTIVE SECTION ---
        st.subheader("🔍 Click a row to see Technical Analysis")
        # Displaying the main table
        event = st.dataframe(
            df[["Stock", "Category", "Status", "Entry", "Target_2"]],
            on_select="rerun",
            selection_mode="single_row",
            use_container_width=True
        )

        # Logic to show analysis when a row is selected
        selection = event.selection.rows
        if selection:
            selected_index = selection[0]
            stock_data = df.iloc[selected_index]
            
            st.info(f"### 📊 Deep Analysis: {stock_data['Stock']}")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("RSI", stock_data['RSI'])
            col_b.metric("Volume Ratio", f"{stock_data['Vol_Ratio']}x")
            col_c.metric("Status", stock_data['Status'])
            
            st.success(f"**Verdict:** {stock_data['Analysis']}")
        else:
            st.write("👆 *Table mein kisi bhi stock par click karo uska logic dekhne ke liye.*")
            
    else:
        st.warning("No signals found.")
