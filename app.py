import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty 200: Smart Strategy Tracker", layout="wide")

# --- NIFTY 200 LIST ---
NIFTY_200 = [
    'ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS'
]

st.title("🛡️ 90% Accuracy Strategy (Click Row for Analysis)")

# --- DATE LOGIC ---
target_date = st.date_input("Analysis Date", datetime(2025, 12, 12))
if target_date.weekday() == 5: target_date -= timedelta(days=1)
if target_date.weekday() == 6: target_date -= timedelta(days=2)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    return 100 - (100 / (1 + (gain / loss)))

def run_scan():
    results = []
    t_ts = pd.Timestamp(target_date)
    prog = st.progress(0)

    for i, ticker in enumerate(NIFTY_200):
        try:
            data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
            if len(data) < 201 or t_ts not in data.index: continue
            
            data['SMA_44'] = data['Close'].rolling(window=44).mean()
            data['SMA_200'] = data['Close'].rolling(window=200).mean()
            data['RSI'] = calculate_rsi(data['Close'])
            data['Vol_Avg'] = data['Volume'].rolling(window=5).mean()
            
            day = data.loc[t_ts]
            close, open_p, low_p = float(day['Close']), float(day['Open']), float(day['Low'])
            sma44, sma200, rsi = float(day['SMA_44']), float(day['SMA_200']), float(day['RSI'])
            vol, vol_avg = float(day['Volume']), float(day['Vol_Avg'])

            if close > sma44 and sma44 > sma200 and close > open_p:
                is_blue = rsi > 65 and vol > vol_avg and (close > sma200 * 1.05)
                risk = close - low_p
                t2 = close + (2 * risk)
                
                status, analysis = "⏳ Running", "Momentum active hai, price SMA ke upar hai."
                future = data[data.index > t_ts]
                
                if not future.empty:
                    for _, f_row in future.iterrows():
                        if f_row['Low'] <= low_p:
                            status, analysis = "🔴 SL Hit", f"Stock fail hua kyunki Signal Low (Support) break hua. RSI {round(rsi,1)} tha."
                            break
                        if f_row['High'] >= t2:
                            status, analysis = "🔥 Jackpot Hit", f"Target 1:2 hit! RSI {round(rsi,1)} aur High Volume ne support diya."
                            break

                pure_name = ticker.replace(".NS","")
                tv_link = f"https://www.tradingview.com/chart/?symbol=NSE:{pure_name}"
                
                results.append({
                    "Stock": pure_name,
                    "Chart 📈": tv_link,
                    "Category": "🔵 BLUE" if is_blue else "🟡 AMBER",
                    "Status": status,
                    "Entry": round(close, 2),
                    "Stoploss": round(low_p, 2),
                    "Target 1:2": round(t2, 2),
                    "Detailed Analysis": analysis # Hidden column for pop-up
                })
        except: continue
        prog.progress((i + 1) / len(NIFTY_200))
    return pd.DataFrame(results)

if st.button('🚀 Start Strategy Scan'):
    df_results = run_scan()
    if not df_results.empty:
        st.subheader(f"📊 Market Report: {target_date}")
        st.write("👇 *Stock ke naam par click karo analysis dekhne ke liye*")

        # --- SMART INTERACTIVE DATAFRAME ---
        # We use on_select to trigger the analysis display
        selection = st.dataframe(
            df_results[["Stock", "Chart 📈", "Category", "Status", "Entry", "Stoploss", "Target 1:2"]],
            column_config={
                "Chart 📈": st.column_config.LinkColumn("TradingView")
            },
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single_row"
        )

        # Checking if a row is clicked
        if selection.selection.rows:
            selected_idx = selection.selection.rows[0]
            selected_stock = df_results.iloc[selected_idx]
            
            # Displaying the analysis right below the table
            st.info(f"### 💡 Analysis for {selected_stock['Stock']}")
            st.success(selected_stock["Detailed Analysis"])
    else:
        st.warning("No signals found.")
