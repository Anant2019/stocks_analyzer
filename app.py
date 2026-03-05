import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 1. PREMIUM PAGE CONFIG ---
st.set_page_config(
    page_title="ArthaSutra | Wealth Creation Engine", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="💹"
)

# --- 2. TERMINAL UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E0E0E0; }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 800; color: #00FFA3 !important; }
    .stButton button {
        border-radius: 8px; padding: 1rem; font-weight: 800;
        background: linear-gradient(90deg, #00FFA3, #00D1FF); color: #0B0E14; border: none;
    }
    .trade-card {
        background-color: #161A23; border: 1px solid #2D3436; border-radius: 12px;
        padding: 15px; margin-bottom: 12px; border-left: 8px solid #8E9AAF;
    }
    .grid-container {
        display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px;
    }
    @media (min-width: 768px) {
        .grid-container { grid-template-columns: repeat(4, 1fr); }
    }
    .shadow-green { border-left-color: #00FFA3 !important; box-shadow: 0 4px 15px rgba(0, 255, 163, 0.15); }
    .shadow-amber { border-left-color: #FFC107 !important; box-shadow: 0 4px 15px rgba(255, 193, 7, 0.15); }
    .shadow-red { border-left-color: #FF4B4B !important; box-shadow: 0 4px 15px rgba(255, 75, 75, 0.15); }
    .trend-tag { padding: 2px 6px; border-radius: 4px; font-size: 0.6rem; font-weight: 800; margin-left: 5px; vertical-align: middle; }
    .blue-bg { background: rgba(0, 123, 255, 0.2); color: #00D1FF; border: 1px solid #00D1FF; }
    .amber-bg { background: rgba(255, 193, 7, 0.2); color: #FFC107; border: 1px solid #FFC107; }
    .rr-label { color: #8E9AAF; font-size: 0.55rem; font-weight: 700; text-transform: uppercase; }
    .rr-value { color: #FFFFFF; font-size: 0.85rem; font-weight: 800; }
    .profit-pct { color: #00FFA3; font-size: 0.65rem; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SEBI COMPLIANT DISCLOSURE (LEGAL UPGRADE) ---
st.markdown("""
    <div style="background: rgba(255, 193, 7, 0.05); border: 1px solid #FFC107; padding: 12px; border-radius: 10px; margin-bottom: 20px;">
        <h4 style="color: #FFC107; margin: 0; font-size: 0.9rem;">⚠️ SEBI MANDATED DISCLOSURE</h4>
        <p style="font-size: 0.75rem; color: #CCCCCC; margin-top: 5px; line-height: 1.4;">
            <b>Investments in securities market are subject to market risks. Read all the related documents carefully before investing.</b> 
            ArthaSutra is an automated quantitative research tool and is <b>NOT SEBI Registered</b>. 
            The signals generated are based on technical indicators (44 SMA Support) and are for educational/research purposes only. 
            Past performance is not indicative of future results. No guaranteed returns are promised.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. DATA ENGINE (MULTI-THREADED) ---
NIFTY_200 = ['ABB.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ATGL.NS', 'AMBUJACEM.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BALKRISIND.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BERGEPAINT.NS', 'BEL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLAND.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIAHOTEL.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IGL.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'INFY.NS', 'IPCALAB.NS', 'JSWSTEEL.NS', 'JSL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LICHSGFIN.NS', 'LICI.NS', 'LUPIN.NS', 'MRF.NS', 'M&M.NS', 'M&MFIN.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MPHASIS.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'PIIND.NS', 'PFC.NS', 'POLY_MED.NS', 'POLYCAB.NS', 'POWARGRID.NS', 'PRESTIGE.NS', 'RELIANCE.NS', 'RVNL.NS', 'RECLTD.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SRF.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACOMM.NS', 'TATAELXSI.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZOMATO.NS', 'ZYDUSLIFE.NS']

def process_stock(ticker, target_date):
    try:
        data = yf.download(ticker, start=target_date - timedelta(days=450), end=datetime.now(), auto_adjust=True, progress=False)
        if len(data) < 205: return None
        if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
        
        v_dates = data.index[data.index.date <= target_date]
        if v_dates.empty: return None
        t_ts = v_dates[-1]
        
        # Indicators (V7 Core)
        data['SMA_44'] = data['Close'].rolling(44).mean()
        data['SMA_200'] = data['Close'].rolling(200).mean()
        data['Vol_MA'] = data['Volume'].rolling(20).mean()
        delta = data['Close'].diff(); gain = delta.where(delta > 0, 0).rolling(14).mean(); loss = -delta.where(delta < 0, 0).rolling(14).mean()
        data['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-10))))

        d = data.loc[t_ts]
        is_44_up = d['SMA_44'] > data['SMA_44'].shift(5).loc[t_ts]
        is_200_up = d['SMA_200'] > data['SMA_200'].shift(5).loc[t_ts]
        on_support = (d['Low'] <= d['SMA_44'] * 1.01)
        strong_rejection = (d['Close'] > d['Open']) and (d['Close'] > d['SMA_44'])
        vol_ok = d['Volume'] > (d['Vol_MA'] * 0.9)

        if is_44_up and is_200_up and on_support and strong_rejection and vol_ok:
            is_blue = d['RSI'] > 55
            sl = round(d['Low'], 2)
            risk = d['Close'] - sl
            if (risk/d['Close']) > 0.06: return None 
            
            t1, t2 = round(d['Close'] + risk, 2), round(d['Close'] + (2*risk), 2)
            t1_p, t2_p = round((risk/d['Close'])*100, 1), round((2*risk/d['Close'])*100, 1)
            
            status, t1_hit, t2_hit, days = "⏳ RUNNING", False, False, "-"
            future = data[data.index > t_ts]
            if not future.empty:
                for count, (f_dt, f_row) in enumerate(future.iterrows(), 1):
                    if f_row['High'] >= t1: t1_hit = True
                    if f_row['High'] >= t2: status = "🟢 JACKPOT"; t2_hit = True; days = count; break
                    if f_row['Low'] <= sl: status = "🔴 SL HIT"; days = count; break
                if status == "⏳ RUNNING" and t1_hit: status = "🟡 1:1 HIT"

            return {
                "Stock": ticker.replace(".NS",""), "Status": status, "Entry": round(d['Close'], 2),
                "SL": sl, "T1": t1, "T2": t2, "T1_P": t1_p, "T2_P": t2_p,
                "T1_H": t1_hit, "T2_H": t2_hit, "Days": days, "RSI": round(d['RSI'], 1),
                "Type": "BLUE" if is_blue else "AMBER",
                "Chart": f"https://www.tradingview.com/chart/?symbol=NSE:{ticker.replace('.NS','')}"
            }
    except: return None
    return None

# --- 5. UI EXECUTION ---
st.title("💹 ArthaSutra | Middle-Class Wealth Engine")
selected_date = st.date_input("Audit Date", datetime.now().date() - timedelta(days=12))

if st.button('🚀 EXECUTE HIGH-ACCURACY SCAN', use_container_width=True):
    progress_bar = st.progress(0)
    card_container = st.container()
    
    # Live stats placeholders
    m1_p = st.sidebar.empty()
    m2_p = st.sidebar.empty()
    m3_p = st.sidebar.empty()
    
    results = []
    total_scanned = 0
    
    # Threaded Execution
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_stock, ticker, selected_date): ticker for ticker in NIFTY_200}
        
        for i, future in enumerate(as_completed(futures)):
            total_scanned += 1
            progress_bar.progress(total_scanned / len(NIFTY_200))
            
            res = future.result()
            if res:
                results.append(res)
                
                # LAZY LOADING: Show cards immediately as found
                with card_container:
                    shadow_class = "shadow-red" if "SL" in res['Status'] else "shadow-green" if "JACKPOT" in res['Status'] else "shadow-amber" if "1:1" in res['Status'] else ""
                    trend_class = "blue-bg" if res['Type'] == "BLUE" else "amber-bg"
                    
                    st.markdown(f"""
                    <div class="trade-card {shadow_class}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 1.1rem; font-weight: 800; color: white;">
                                {res['Stock']}<span class="trend-tag {trend_class}">{res['Type']}</span>
                            </span>
                            <span style="font-weight:900; font-size: 0.8rem; color:{'#00FFA3' if 'JACKPOT' in res['Status'] else '#FF4B4B' if 'SL' in res['Status'] else '#FFC107'};">{res['Status']}</span>
                        </div>
                        <div class="grid-container">
                            <div><div class="rr-label">Entry</div><div class="rr-value">₹{res['Entry']}</div></div>
                            <div><div class="rr-label" style="color:#FF7E7E;">SL</div><div class="rr-value">₹{res['SL']}</div></div>
                            <div><div class="rr-label" style="color:#00FFA3;">T1 (1:1)</div><div class="rr-value">₹{res['T1']}</div><div class="profit-pct">+{res['T1_P']}%</div></div>
                            <div><div class="rr-label" style="color:#00D1FF;">T2 (1:2)</div><div class="rr-value">₹{res['T2']}</div><div class="profit-pct">+{res['T2_P']}%</div></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander(f"Quick View: {res['Stock']}"):
                        st.write(f"RSI: {res['RSI']} | Days to Hit: {res['Days']}")
                        st.link_button("View Live Chart 📈", res['Chart'], use_container_width=True)

    # Final summary update
    if results:
        df_final = pd.DataFrame(results)
        t1_acc = (len(df_final[df_final['T1_H'] == True]) / len(df_final)) * 100
        t2_acc = (len(df_final[df_final['T2_H'] == True]) / len(df_final)) * 100
        
        st.divider()
        st.subheader("Final Audit Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("🎯 1:1 Accuracy", f"{round(t1_acc, 1)}%")
        m2.metric("💎 1:2 Accuracy", f"{round(t2_acc, 1)}%")
        m3.metric("📈 Total Signals", len(df_final))
    else:
        st.warning("No high-probability support setups found on this date.")
