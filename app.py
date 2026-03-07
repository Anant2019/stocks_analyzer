"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ARTHSUTRA v8 — Only TP Hitters                                              ║
║  Shows ONLY stocks where this exact Pine Script setup                        ║
║  has historically hit TP1/TP2 on that specific stock                        ║
║                                                                              ║
║  HOW IT WORKS:                                                               ║
║  Step 1 — For each stock, look back 90 days                                 ║
║           Find every past occurrence of the Pine Script signal               ║
║           Count how many hit TP1, TP2, SL                                   ║
║  Step 2 — Only show today's signal if that stock's                          ║
║           historical TP hit rate passes the threshold                        ║
║  Step 3 — Rank by TP hit rate (best stock first)                            ║
║                                                                              ║
║  RESULT: Every signal shown has EVIDENCE it tends to work on that stock.    ║
║  NOT SEBI Registered · Educational Use Only                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

INSTALL:  pip install streamlit pandas numpy yfinance
RUN:      streamlit run arthsutra.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import math, io, time
from datetime import date, timedelta, datetime

try:
    import yfinance as yf
    YF_OK = True
except ImportError:
    YF_OK = False

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Arthsutra · Only TP Hitters",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif!important;background:#020912!important;color:#c2dcf0!important;}
#MainMenu,footer,header{visibility:hidden;} .stDeployButton{display:none;}
.block-container{padding-top:.7rem!important;padding-bottom:3rem!important;max-width:1380px!important;}
::-webkit-scrollbar{width:4px;} ::-webkit-scrollbar-thumb{background:#0c1e30;border-radius:4px;}

div[data-testid="metric-container"]{background:#050f1c!important;border:1px solid #0b1d2e!important;border-radius:12px!important;padding:14px 18px!important;}
div[data-testid="metric-container"] label{font-family:'JetBrains Mono',monospace!important;font-size:8px!important;letter-spacing:2px!important;color:#142840!important;text-transform:uppercase!important;}
div[data-testid="stMetricValue"]{font-size:22px!important;font-weight:700!important;color:#d6ecff!important;}
div[data-testid="stMetricDelta"]{font-family:'JetBrains Mono',monospace!important;font-size:10px!important;}

.stButton>button{font-family:'Space Grotesk',sans-serif!important;font-weight:700!important;background:linear-gradient(135deg,#15803d,#16a34a)!important;color:white!important;border:none!important;border-radius:10px!important;padding:.6rem 2rem!important;font-size:14px!important;transition:all .2s!important;}
.stButton>button:hover{background:linear-gradient(135deg,#16a34a,#22c55e)!important;box-shadow:0 6px 22px rgba(22,163,74,.4)!important;transform:translateY(-1px)!important;}
.stSelectbox div[data-baseweb="select"]>div,.stNumberInput input,.stDateInput input{background:#050f1c!important;border:1.5px solid #0b1d2e!important;border-radius:9px!important;color:#c2dcf0!important;font-family:'JetBrains Mono',monospace!important;font-size:13px!important;}
.stTabs [data-baseweb="tab-list"]{background:#050f1c!important;border-radius:10px!important;padding:4px!important;gap:4px!important;border:1px solid #0b1d2e!important;}
.stTabs [data-baseweb="tab"]{font-family:'Space Grotesk',sans-serif!important;font-weight:500!important;font-size:13px!important;color:#163050!important;border-radius:8px!important;padding:7px 18px!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#15803d,#16a34a)!important;color:white!important;font-weight:700!important;}
.streamlit-expanderHeader{font-family:'Space Grotesk',sans-serif!important;font-weight:600!important;background:#020912!important;border:1px solid #0b1d2e!important;border-radius:10px!important;color:#3a7a9a!important;}
.streamlit-expanderContent{background:#020912!important;border:1px solid #0b1d2e!important;border-top:none!important;border-radius:0 0 10px 10px!important;}
.stDataFrame{border:1px solid #0b1d2e!important;border-radius:10px!important;}
hr{border-color:#0b1d2e!important;margin:.8rem 0!important;}
.stInfo{background:rgba(22,163,74,.06)!important;border:1px solid rgba(22,163,74,.2)!important;border-radius:10px!important;}
.stWarning{background:rgba(234,179,8,.06)!important;border:1px solid rgba(234,179,8,.18)!important;border-radius:10px!important;}
.stSuccess{background:rgba(22,163,74,.09)!important;border:1px solid rgba(22,163,74,.26)!important;border-radius:10px!important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# NSE 200
# ─────────────────────────────────────────────────────────────────────────────
NSE200 = [
    "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","BHARTIARTL","SBIN","HINDUNILVR",
    "ITC","BAJFINANCE","KOTAKBANK","LT","AXISBANK","MARUTI","SUNPHARMA","TITAN",
    "WIPRO","ULTRACEMCO","NTPC","ADANIPORTS","BAJAJ-AUTO","HCLTECH","ONGC","TATAMOTORS",
    "DIVISLAB","DRREDDY","JSWSTEEL","COALINDIA","BPCL","GRASIM","TECHM","ZOMATO",
    "TRENT","HAL","BEL","DLF","SIEMENS","CHOLAFIN","NESTLEIND","TATAPOWER",
    "POWERGRID","CIPLA","HINDALCO","DABUR","GODREJCP","AMBUJACEM","TATACONSUM",
    "BRITANNIA","PIDILITIND","MPHASIS","PERSISTENT","LTTS","COFORGE","KPITTECH",
    "OFSS","CANBK","PNB","BANKBARODA","FEDERALBNK","IDFCFIRSTB","INDUSINDBK",
    "AUBANK","ABCAPITAL","MUTHOOTFIN","MANAPPURAM","LICHSGFIN","EICHER",
    "HEROMOTOCO","TVSMOTORS","ASHOKLEY","M&M","ESCORTS","BOSCHLTD","ENDURANCE",
    "BHARATFORG","LUPIN","TORNTPHARM","ALKEM","IPCALAB","NATCOPHARM","GRANULES",
    "AJANTPHARM","LAURUSLABS","AUROPHARMA","GLENMARK","BIOCON","NMDC","HINDCOPPER",
    "VEDL","NATIONALUM","MOIL","AIAENG","ASTRAL","SUPREMEIND","RELAXO","BATA",
    "PAGEIND","DMART","ABFRL","HAVELLS","POLYCAB","KEI","CDSL","MCX","ANGELONE",
    "PIIND","BERGEPAINT","COLPAL","MARICO","SBILIFE","ICICIGI","HDFCLIFE",
    "BAJAJFINSV","ADANIENT","ADANIGREEN","MOTHERSON","YESBANK","BANDHANBNK",
    "RBLBANK","SHRIRAMFIN","SUNDARMFIN","PNBHOUSING","CANFINHOME","TIINDIA",
    "PFIZER","ABBOTINDIA","GLAXO","CARBORUNIV","GRINDWELL","NILKAMAL","CAMPUS",
    "BLUESTAR","CROMPTON","FINOLEX","RAYMOND","VARDHMAN","TRIDENT","WELSPUN",
    "SHREECEM","RAMCOCEM","JKCEMENT","NUVAMA","UJJIVAN","SURYODAY","EQUITASBNK",
    "DCBBANK","KARURVSYS","FORCEMOT","WHIRLPOOL","VOLTAS",
]
NSE200 = list(dict.fromkeys(NSE200))

def yf_sym(t): return f"{t}.NS"

# ─────────────────────────────────────────────────────────────────────────────
# INDICATORS
# ─────────────────────────────────────────────────────────────────────────────
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["sma44"]    = df["Close"].rolling(44,  min_periods=44).mean()
    df["sma200"]   = df["Close"].rolling(200, min_periods=200).mean()
    df["sma44_2"]  = df["sma44"].shift(2)
    df["sma200_2"] = df["sma200"].shift(2)
    return df

# ─────────────────────────────────────────────────────────────────────────────
# PINE SCRIPT SIGNAL — exact port
# ─────────────────────────────────────────────────────────────────────────────
def pine_signal(row: pd.Series) -> dict | None:
    needed = ["Close","Open","High","Low","sma44","sma200","sma44_2","sma200_2"]
    if any(pd.isna(row.get(c, np.nan)) for c in needed):
        return None

    c, o, h, l   = float(row.Close), float(row.Open), float(row.High), float(row.Low)
    s44, s200     = float(row.sma44), float(row.sma200)
    s44_2, s200_2 = float(row.sma44_2), float(row.sma200_2)

    is_trending = s44 > s200 and s44 > s44_2 and s200 > s200_2
    is_strong   = c > o and c > (h + l) / 2
    buy         = is_trending and is_strong and l <= s44 and c > s44

    if not buy:
        return None

    risk = c - l
    if risk <= 0 or risk / c > 0.15:
        return None

    return {
        "entry":    round(c, 2),
        "sl":       round(l, 2),
        "tp1":      round(c + risk, 2),
        "tp2":      round(c + risk * 2, 2),
        "risk":     round(risk, 2),
        "risk_pct": round(risk / c * 100, 2),
        "sma44":    round(s44, 2),
        "sma200":   round(s200, 2),
        "gap_pct":  round((s44 - s200) / s200 * 100, 2),
    }

# ─────────────────────────────────────────────────────────────────────────────
# FORWARD OUTCOME
# ─────────────────────────────────────────────────────────────────────────────
def resolve_outcome(fwd: pd.DataFrame, entry, sl, tp1, tp2, max_days=20) -> str:
    for _, r in fwd.head(max_days).iterrows():
        hi, lo = float(r.High), float(r.Low)
        if lo <= sl:  return "SL"
        if hi >= tp2: return "TP2"
        if hi >= tp1: return "TP1"
    return "RUNNING"

# ─────────────────────────────────────────────────────────────────────────────
# PER-STOCK HISTORICAL TP HIT RATE
# Look back over all past signals on THIS stock and count TP hits
# ─────────────────────────────────────────────────────────────────────────────
def compute_stock_history(ind: pd.DataFrame, raw: pd.DataFrame,
                          lookback_days: int = 90) -> dict:
    """
    Walk every row in the last `lookback_days` of ind.
    For each Pine signal fired, resolve outcome from real forward prices.
    Returns { n_signals, n_tp1, n_tp2, n_sl, tp1_rate, tp2_rate, sl_rate }
    """
    all_dates = list(ind.index)
    if len(all_dates) < 2:
        return {}

    cutoff  = all_dates[-1] - timedelta(days=lookback_days)
    # Exclude the last row (that's today's signal — don't count it in history)
    hist_dates = [d for d in all_dates[:-1] if d >= cutoff]

    n_sig = n_tp1 = n_tp2 = n_sl = 0

    for sig_date in hist_dates:
        row = ind.loc[sig_date]
        sig = pine_signal(row)
        if sig is None:
            continue

        fwd = raw[raw.index > sig_date]
        if fwd.empty:
            continue

        out = resolve_outcome(fwd, sig["entry"], sig["sl"], sig["tp1"], sig["tp2"])
        if out == "RUNNING":
            continue   # skip unresolved past signals

        n_sig += 1
        if out == "TP2":       n_tp2 += 1; n_tp1 += 1
        elif out == "TP1":     n_tp1 += 1
        elif out == "SL":      n_sl  += 1

    if n_sig == 0:
        return {"n_signals": 0, "n_tp1": 0, "n_tp2": 0, "n_sl": 0,
                "tp1_rate": 0.0, "tp2_rate": 0.0, "sl_rate": 0.0}

    return {
        "n_signals": n_sig,
        "n_tp1":     n_tp1,
        "n_tp2":     n_tp2,
        "n_sl":      n_sl,
        "tp1_rate":  round(n_tp1 / n_sig * 100, 1),
        "tp2_rate":  round(n_tp2 / n_sig * 100, 1),
        "sl_rate":   round(n_sl  / n_sig * 100, 1),
    }

# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCANNER
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def run_scan(scan_date_str: str,
             min_tp1_rate: float,
             min_tp2_rate: float,
             min_hist_signals: int,
             max_sl_risk_pct: float = 3.0) -> pd.DataFrame:
    """
    DUAL FILTER — both must pass:
      A. TIGHT SL: today's candle risk% <= max_sl_risk_pct  (e.g. ≤ 3%)
      B. HISTORY:  this stock's past 90-day TP1 rate >= min_tp1_rate (e.g. ≥ 80%)
                   AND past TP2 rate >= min_tp2_rate
                   AND at least min_hist_signals past occurrences exist
    Returns DataFrame sorted by tp2_rate desc, then tp1_rate, then tightest SL.
    """
    scan_date = datetime.strptime(scan_date_str, "%Y-%m-%d").date()
    # Need 200 bars + 90-day lookback + 20 forward days
    dl_start  = scan_date - timedelta(days=400)
    dl_end    = scan_date + timedelta(days=30)

    results = []
    prog = st.progress(0, text="Scanning stocks…")

    for i, ticker in enumerate(NSE200):
        prog.progress((i + 1) / len(NSE200), text=f"Analysing {ticker} ({i+1}/{len(NSE200)})…")
        try:
            raw = yf.download(
                yf_sym(ticker),
                start=dl_start, end=dl_end,
                progress=False, auto_adjust=True,
            )
            if raw.empty or len(raw) < 215:
                continue
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            raw.index = pd.to_datetime(raw.index).date

            # History up to scan_date, forward data after
            hist = raw[raw.index <= scan_date]
            fwd  = raw[raw.index >  scan_date]
            if len(hist) < 215:
                continue

            ind   = add_indicators(hist)
            avail = [d for d in ind.index if d <= scan_date]
            if not avail:
                continue

            today_row = ind.loc[max(avail)]

            # ── Check if TODAY fires the signal ───────────────────────────
            sig = pine_signal(today_row)
            if sig is None:
                continue   # no signal today → skip entirely

            # ── GATE: tight SL — risk must be within max_sl_risk_pct ──────
            if sig["risk_pct"] > max_sl_risk_pct:
                continue   # SL too wide → high chance of being stopped out

            # ── Historical TP rate for THIS stock ─────────────────────────
            hist_stats = compute_stock_history(ind, raw, lookback_days=90)

            n_hist = hist_stats.get("n_signals", 0)
            tp1_r  = hist_stats.get("tp1_rate", 0.0)
            tp2_r  = hist_stats.get("tp2_rate", 0.0)
            sl_r   = hist_stats.get("sl_rate",  0.0)

            # ── Apply thresholds ──────────────────────────────────────────
            if n_hist < min_hist_signals:
                continue   # not enough history to trust
            if tp1_r < min_tp1_rate:
                continue   # historically doesn't hit TP1 enough
            if tp2_r < min_tp2_rate:
                continue   # historically doesn't hit TP2 enough

            # ── Resolve today's outcome (for backtesting context) ─────────
            out_full = {}
            if not fwd.empty:
                out_str = resolve_outcome(fwd, sig["entry"], sig["sl"], sig["tp1"], sig["tp2"])
                exit_p  = (sig["tp2"] if out_str=="TP2" else
                           sig["tp1"] if out_str=="TP1" else
                           sig["sl"]  if out_str=="SL"  else float(fwd.Close.iloc[-1]))
                days_to = next(
                    (j+1 for j,(_, r) in enumerate(fwd.head(20).iterrows())
                     if (float(r.Low) <= sig["sl"] or
                         float(r.High) >= sig["tp1"])),
                    len(fwd.head(20))
                )
                out_full = {"outcome": out_str, "days": days_to, "exit_price": exit_p}
            else:
                out_full = {"outcome": "LIVE", "days": 0, "exit_price": sig["entry"]}

            results.append({
                "ticker":        ticker,
                "entry":         sig["entry"],
                "sl":            sig["sl"],
                "tp1":           sig["tp1"],
                "tp2":           sig["tp2"],
                "risk_pct":      sig["risk_pct"],
                "sma44":         sig["sma44"],
                "sma200":        sig["sma200"],
                "gap_pct":       sig["gap_pct"],
                # Historical evidence
                "hist_signals":  n_hist,
                "hist_tp1_rate": tp1_r,
                "hist_tp2_rate": tp2_r,
                "hist_sl_rate":  sl_r,
                # Today's outcome (if available)
                "outcome":       out_full["outcome"],
                "days":          out_full["days"],
                "exit_price":    out_full["exit_price"],
            })

        except Exception:
            pass

        if i % 20 == 0 and i > 0:
            time.sleep(0.1)

    prog.empty()

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    # Sort by TP2 hit rate (most reliable first), then TP1, then tightest SL
    df = df.sort_values(
        ["hist_tp2_rate", "hist_tp1_rate", "risk_pct"],
        ascending=[False, False, True]
    ).reset_index(drop=True)
    return df

# ─────────────────────────────────────────────────────────────────────────────
# FORMATTING
# ─────────────────────────────────────────────────────────────────────────────
def fmt(v: float) -> str:
    return f"₹{v:,.2f}"

def rate_col(v: float, green_thresh: float, yellow_thresh: float) -> str:
    return "#22c55e" if v >= green_thresh else ("#f59e0b" if v >= yellow_thresh else "#ef4444")

OUTCOME_DISP = {
    "TP2":     ("🎯", "#22c55e", "TP2 Hit · 1:2"),
    "TP1":     ("✅", "#f59e0b", "TP1 Hit · 1:1"),
    "SL":      ("🛑", "#ef4444", "SL Hit"),
    "RUNNING": ("⏳", "#38bdf8", "Still Running"),
    "LIVE":    ("📡", "#a78bfa", "Live Signal"),
}

# ─────────────────────────────────────────────────────────────────────────────
# HISTORY MINI BAR — visual representation of past TP/SL record
# ─────────────────────────────────────────────────────────────────────────────
def history_bar(tp2_r, tp1_r, sl_r, n_sigs) -> str:
    # Stacked bar: TP2 (green), TP1-only (yellow), SL (red), other (grey)
    tp1_only = max(0, tp1_r - tp2_r)
    other    = max(0, 100 - tp2_r - tp1_only - sl_r)
    return f"""
<div style="margin-bottom:3px;">
  <div style="display:flex;height:8px;border-radius:4px;overflow:hidden;background:#0b1d2e;">
    <div style="width:{tp2_r}%;background:#22c55e;" title="TP2: {tp2_r:.0f}%"></div>
    <div style="width:{tp1_only}%;background:#f59e0b;" title="TP1 only: {tp1_only:.0f}%"></div>
    <div style="width:{sl_r}%;background:#ef4444;" title="SL: {sl_r:.0f}%"></div>
    <div style="width:{other}%;background:#1a3a55;" title="Running: {other:.0f}%"></div>
  </div>
  <div style="display:flex;justify-content:space-between;margin-top:3px;">
    <span style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#22c55e;">TP2 {tp2_r:.0f}%</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#f59e0b;">TP1 {tp1_r:.0f}%</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#ef4444;">SL {sl_r:.0f}%</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#1a3a55;">{n_sigs} past signals</span>
  </div>
</div>"""

# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL CARD
# ─────────────────────────────────────────────────────────────────────────────
def signal_card(row: pd.Series) -> str:
    icon, ocol, olbl = OUTCOME_DISP.get(row["outcome"], OUTCOME_DISP["LIVE"])
    sl_pct  = round((row["entry"] - row["sl"])  / row["entry"] * 100, 2)
    tp1_pct = round((row["tp1"]   - row["entry"])/ row["entry"] * 100, 2)
    tp2_pct = round((row["tp2"]   - row["entry"])/ row["entry"] * 100, 2)
    d       = int(row["days"])
    d_s     = f"{d}d" if row["outcome"] not in ("RUNNING","LIVE") else ("live" if row["outcome"]=="LIVE" else "open")

    tp2_c   = rate_col(row["hist_tp2_rate"], 60, 45)
    tp1_c   = rate_col(row["hist_tp1_rate"], 75, 60)
    sl_c    = rate_col(100 - row["hist_sl_rate"], 85, 70)   # inverted: low SL = green

    return f"""
<div style="background:#050f1c;border:1px solid #0b1d2e;border-top:3px solid #22c55e;
            border-radius:13px;padding:17px 15px 14px;">

  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:11px;">
    <div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">
        <span style="font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:800;color:#d6ecff;">{row["ticker"]}</span>
        <span style="background:rgba(34,197,94,.12);color:#22c55e;font-family:'JetBrains Mono',monospace;
                     font-size:7.5px;font-weight:700;letter-spacing:1.5px;padding:2px 8px;border-radius:4px;">
          HIGH PROBABILITY
        </span>
      </div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#0c1e30;">
        SMA44={fmt(row["sma44"])} &nbsp;·&nbsp; GAP +{row["gap_pct"]}%
      </span>
    </div>
    <a href="https://www.tradingview.com/chart/?symbol=NSE:{row['ticker']}" target="_blank"
       style="background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.2);border-radius:6px;
              padding:4px 9px;font-family:'JetBrains Mono',monospace;font-size:8px;color:#4ade80;text-decoration:none;">↗ TV</a>
  </div>

  <!-- Historical evidence — the KEY differentiator -->
  <div style="background:#020912;border:1px solid #0f2a3f;border-radius:9px;padding:10px 12px;margin-bottom:11px;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#0f2a3f;margin-bottom:7px;">
      📊 THIS STOCK'S PAST 90-DAY RECORD (same setup)
    </div>
    {history_bar(row["hist_tp2_rate"], row["hist_tp1_rate"], row["hist_sl_rate"], int(row["hist_signals"]))}
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:8px;">
      <div style="background:#050f1c;border-radius:6px;padding:7px;border:1px solid {tp2_c}25;text-align:center;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:7px;color:#0f2a3f;margin-bottom:2px;">TP2 HIT</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:{tp2_c};line-height:1;">{row["hist_tp2_rate"]:.0f}%</div>
      </div>
      <div style="background:#050f1c;border-radius:6px;padding:7px;border:1px solid {tp1_c}25;text-align:center;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:7px;color:#0f2a3f;margin-bottom:2px;">TP1 HIT</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:{tp1_c};line-height:1;">{row["hist_tp1_rate"]:.0f}%</div>
      </div>
      <div style="background:#050f1c;border-radius:6px;padding:7px;border:1px solid #ef444425;text-align:center;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:7px;color:#0f2a3f;margin-bottom:2px;">SL HIT</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:#ef4444;line-height:1;">{row["hist_sl_rate"]:.0f}%</div>
      </div>
    </div>
  </div>

  <!-- Price levels -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:10px;">
    <div style="background:#020912;border-radius:7px;padding:8px 10px;border:1px solid #0b1d2e;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:6.5px;letter-spacing:2px;color:#0c1e30;margin-bottom:2px;">ENTRY (close)</div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#d6ecff;">{fmt(row["entry"])}</span>
    </div>
    <div style="background:#020912;border-radius:7px;padding:8px 10px;border:1px solid #0b1d2e;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:6.5px;letter-spacing:2px;color:#0c1e30;margin-bottom:2px;">SL (candle low) <span style="color:#ef4444;">−{sl_pct}%</span></div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#ef4444;">{fmt(row["sl"])}</span>
    </div>
    <div style="background:#020912;border-radius:7px;padding:8px 10px;border:1px solid #0b1d2e;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:6.5px;letter-spacing:2px;color:#0c1e30;margin-bottom:2px;">TARGET 1 · 1:1 <span style="color:#f59e0b;">+{tp1_pct}%</span></div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#f59e0b;">{fmt(row["tp1"])}</span>
    </div>
    <div style="background:#020912;border-radius:7px;padding:8px 10px;border:1px solid #0b1d2e;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:6.5px;letter-spacing:2px;color:#0c1e30;margin-bottom:2px;">TARGET 2 · 1:2 <span style="color:#22c55e;">+{tp2_pct}%</span></div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#22c55e;">{fmt(row["tp2"])}</span>
    </div>
  </div>

  <!-- Outcome badge -->
  <div style="background:#020912;border:1px solid {ocol}20;border-left:3px solid {ocol};
              border-radius:7px;padding:8px 11px;display:flex;align-items:center;justify-content:space-between;">
    <div style="display:flex;align-items:center;gap:6px;">
      <span style="font-size:13px;">{icon}</span>
      <span style="font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:700;color:{ocol};">{olbl}</span>
    </div>
    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#0c1e30;">{d_s}</span>
  </div>
</div>"""

# ─────────────────────────────────────────────────────────────────────────────
# POSITION CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────
def pos_calc(entry, sl, tp1, tp2, capital, risk_pct) -> str:
    rp = entry - sl
    if rp <= 0: return ""
    risk_amt = capital * (risk_pct / 100)
    qty      = max(1, int(risk_amt / rp))
    deployed = qty * entry
    max_loss = qty * rp
    tp1_g    = qty * (tp1 - entry)
    tp2_g    = qty * (tp2 - entry)

    def r(lbl, val, c="#3a7a9a"):
        return (f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #0b1d2e;">'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:8.5px;letter-spacing:1.5px;color:#142840;">{lbl}</span>'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:13px;font-weight:700;color:{c};">{val}</span></div>')

    return f"""<div style="background:#020912;border-radius:10px;padding:13px 15px;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2px;color:#142840;margin-bottom:9px;">POSITION CALCULATOR</div>
  {r("QUANTITY",             f"{qty:,} shares",  "#d6ecff")}
  {r("CAPITAL DEPLOYED",     fmt(deployed),       "#d6ecff")}
  {r("MAX LOSS (SL hit)",    fmt(max_loss),       "#ef4444")}
  {r("PROFIT AT TP1 (1:1)",  fmt(tp1_g),         "#f59e0b")}
  {r("PROFIT AT TP2 (1:2)",  fmt(tp2_g),         "#22c55e")}
  {r("RETURN AT TP1",        f"{tp1_g/deployed*100:.2f}%", "#f59e0b")}
  {r("RETURN AT TP2",        f"{tp2_g/deployed*100:.2f}%", "#22c55e")}
</div>"""

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY BANNER
# ─────────────────────────────────────────────────────────────────────────────
def summary_banner(df: pd.DataFrame, min_tp1: float, min_tp2: float):
    closed = df[df["outcome"].isin(["TP2","TP1","SL"])]
    n = len(closed)

    avg_tp2h = df["hist_tp2_rate"].mean() if len(df) else 0
    avg_tp1h = df["hist_tp1_rate"].mean() if len(df) else 0
    avg_slh  = df["hist_sl_rate"].mean()  if len(df) else 0

    if n > 0:
        actual_tp2 = (closed["outcome"]=="TP2").sum()/n*100
        actual_tp1 = closed["outcome"].isin(["TP1","TP2"]).sum()/n*100
        actual_sl  = (closed["outcome"]=="SL").sum()/n*100
        actual_block = f"""
    <div style="background:#020912;border:1px solid #22c55e25;border-radius:10px;padding:12px 16px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142840;margin-bottom:8px;">ACTUAL OUTCOMES (this scan date)</div>
      <div style="display:flex;gap:16px;">
        <div><div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#142840;">TP2</div>
             <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:#22c55e;">{actual_tp2:.0f}%</div></div>
        <div><div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#142840;">TP1</div>
             <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:#f59e0b;">{actual_tp1:.0f}%</div></div>
        <div><div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#142840;">SL</div>
             <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:#ef4444;">{actual_sl:.0f}%</div></div>
        <div><div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#142840;">CLOSED</div>
             <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:#38bdf8;">{n}</div></div>
      </div>
    </div>"""
    else:
        actual_block = """<div style="background:#020912;border:1px solid #0b1d2e;border-radius:10px;padding:12px 16px;color:#142840;font-family:'JetBrains Mono',monospace;font-size:9px;">
      Actual outcomes not yet resolved (scan date too recent). Use a date ≥5 days ago to see outcomes.
    </div>"""

    st.markdown(f"""
<div style="background:#050f1c;border:1px solid #0b1d2e;border-radius:14px;padding:18px 22px;margin-bottom:14px;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2px;color:#142840;margin-bottom:4px;">
    FILTERED RESULTS · {len(df)} STOCKS QUALIFY · MINIMUM TP1 ≥ {min_tp1:.0f}% · TP2 ≥ {min_tp2:.0f}% HISTORICALLY
  </div>
  <div style="font-family:'Space Grotesk',sans-serif;font-size:11.5px;color:#0b1d2e;margin-bottom:14px;">
    Only stocks with verified historical TP hit rates above your threshold are shown below.
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-bottom:12px;">
    <div style="background:#020912;border:1px solid #22c55e22;border-radius:9px;padding:12px;text-align:center;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142840;margin-bottom:4px;">AVG HIST TP2</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:#22c55e;">{avg_tp2h:.0f}%</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#142840;">across shown stocks</div>
    </div>
    <div style="background:#020912;border:1px solid #f59e0b22;border-radius:9px;padding:12px;text-align:center;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142840;margin-bottom:4px;">AVG HIST TP1</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:#f59e0b;">{avg_tp1h:.0f}%</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#142840;">across shown stocks</div>
    </div>
    <div style="background:#020912;border:1px solid #ef444422;border-radius:9px;padding:12px;text-align:center;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142840;margin-bottom:4px;">AVG HIST SL</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:#ef4444;">{avg_slh:.0f}%</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#142840;">controlled losses</div>
    </div>
    <div style="background:#020912;border:1px solid #38bdf822;border-radius:9px;padding:12px;text-align:center;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142840;margin-bottom:4px;">SIGNALS TODAY</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:#38bdf8;">{len(df)}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#142840;">of 200 scanned</div>
    </div>
  </div>
  {actual_block}
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
def header():
    st.markdown(f"""
<div style="background:#020912;border-bottom:1px solid #0b1d2e;padding:12px 0 9px;margin-bottom:12px;">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="width:44px;height:44px;border-radius:11px;
                  background:linear-gradient(135deg,#15803d,#0f766e);
                  display:flex;align-items:center;justify-content:center;font-size:22px;
                  box-shadow:0 0 20px rgba(21,128,61,.3);">🎯</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:#d6ecff;">Arthsutra</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2.5px;color:#0b1d2e;margin-top:2px;">
          ONLY TP HITTERS · TP1 ≥80% HISTORY + TIGHT SL ≤3% · SMA44/200
        </div>
      </div>
    </div>
    <div style="display:flex;gap:7px;flex-wrap:wrap;">
      <div style="background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.18);
                  border-radius:8px;padding:6px 13px;">
        <span style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:1.5px;color:#22c55e;">✅ HISTORY VERIFIED</span>
      </div>
      <div style="background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.18);
                  border-radius:8px;padding:6px 13px;">
        <span style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:1.5px;color:#ef4444;">🔒 TIGHT SL ≤ 3%</span>
      </div>
    </div>
  </div>
  <div style="background:rgba(234,179,8,.04);border:1px solid rgba(234,179,8,.12);
              border-radius:8px;padding:6px 13px;margin-top:10px;">
    <span style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#5a4a18;">
      ⚠ NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · PAST TP HIT RATES DO NOT GUARANTEE FUTURE RESULTS
    </span>
  </div>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    for k in ["df","scan_done"]:
        if k not in st.session_state:
            st.session_state[k] = None

    header()

    if not YF_OK:
        st.error("❌ **yfinance not installed.**\n\n```\npip install yfinance\n```")
        st.stop()

    # ── Controls ──────────────────────────────────────────────────────────────
    st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#142840;margin-bottom:5px;">SCAN SETTINGS</p>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([2, 1.2, 1.2, 1.6, 1.4])

    with c1:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#142840;margin-bottom:4px;">SIGNAL DATE</p>', unsafe_allow_html=True)
        today   = date.today()
        default = today - timedelta(days=4)
        while default.weekday() >= 5: default -= timedelta(days=1)
        sel_date = st.date_input("_d", value=default,
                                 min_value=today - timedelta(days=200),
                                 max_value=today - timedelta(days=1),
                                 label_visibility="collapsed")

    with c2:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#142840;margin-bottom:4px;">MIN HIST TP1% <span style="color:#22c55e;">★</span></p>', unsafe_allow_html=True)
        min_tp1 = st.number_input("_t1", value=80.0, min_value=50.0, max_value=100.0,
                                  step=5.0, label_visibility="collapsed")

    with c3:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#142840;margin-bottom:4px;">MIN HIST TP2%</p>', unsafe_allow_html=True)
        min_tp2 = st.number_input("_t2", value=55.0, min_value=30.0, max_value=100.0,
                                  step=5.0, label_visibility="collapsed")

    with c4:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#142840;margin-bottom:4px;">MAX SL RISK% <span style="color:#ef4444;">↓</span></p>', unsafe_allow_html=True)
        max_sl_risk = st.number_input("_sr", value=3.0, min_value=0.5, max_value=8.0,
                                      step=0.5, label_visibility="collapsed",
                                      help="Only show signals where SL is within this % of entry. Tighter = safer.")

    with c5:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#142840;margin-bottom:4px;">MIN PAST SIGNALS</p>', unsafe_allow_html=True)
        min_hist = st.number_input("_mh", value=3, min_value=1, max_value=10,
                                   step=1, label_visibility="collapsed",
                                   help="Min past occurrences needed to trust the TP rate stat")

    _, rb = st.columns([6, 1.4])
    with rb:
        run = st.button("🎯  Find TP Hitters", use_container_width=True)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── Run ───────────────────────────────────────────────────────────────────
    if run:
        st.info(f"🔍 Scanning NSE 200 for **{sel_date}** — TP1 ≥ {min_tp1:.0f}% historically AND SL risk ≤ {max_sl_risk:.1f}%. ~4 min first run.")
        df = run_scan(str(sel_date), float(min_tp1), float(min_tp2), int(min_hist), float(max_sl_risk))
        st.session_state["df"]        = df
        st.session_state["scan_done"] = str(sel_date)

        if df is None or df.empty:
            st.warning(
                f"⚠ No stocks passed both filters on this date.\n\n"
                f"**Filter A — Tight SL:** candle risk ≤ {max_sl_risk:.1f}% of entry\n"
                f"**Filter B — History:** TP1 ≥ {min_tp1:.0f}% and TP2 ≥ {min_tp2:.0f}% on this stock in last 90 days\n\n"
                f"**Try relaxing:**\n"
                f"- Raise Max SL Risk% to 4–5%\n"
                f"- Lower Min Hist TP1% to 70%\n"
                f"- Reduce Min Past Signals to 2\n"
                f"- Try a bull-trend date (e.g. Jan–Mar 2024)"
            )
            return
        st.success(f"✅ **{len(df)} stocks** fire today's signal AND have historically hit TP1/TP2 above your thresholds.")

    df = st.session_state["df"]

    # ── Idle ──────────────────────────────────────────────────────────────────
    if df is None or df.empty:
        st.markdown("""
<div style="text-align:center;padding:52px 0 62px;">
  <div style="font-size:52px;opacity:0.07;margin-bottom:14px;">🎯</div>
  <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:700;color:#0b1d2e;margin-bottom:14px;">
    Only TP Hitters · History-Verified Signals
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;max-width:560px;margin:0 auto 18px;">
    <div style="background:#050f1c;border:1px solid #22c55e18;border-radius:10px;padding:14px 10px;text-align:center;">
      <div style="font-size:22px;margin-bottom:6px;">1️⃣</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#22c55e;letter-spacing:1px;margin-bottom:4px;">TODAY'S SIGNAL</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:11.5px;color:#142840;line-height:1.5;">Pine Script fires on this stock today</div>
    </div>
    <div style="background:#050f1c;border:1px solid #a78bfa18;border-radius:10px;padding:14px 10px;text-align:center;">
      <div style="font-size:22px;margin-bottom:6px;">2️⃣</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#a78bfa;letter-spacing:1px;margin-bottom:4px;">90-DAY HISTORY</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:11.5px;color:#142840;line-height:1.5;">Same setup on this stock historically hit TP</div>
    </div>
    <div style="background:#050f1c;border:1px solid #22c55e18;border-radius:10px;padding:14px 10px;text-align:center;">
      <div style="font-size:22px;margin-bottom:6px;">3️⃣</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#22c55e;letter-spacing:1px;margin-bottom:4px;">RANKED BY TP RATE</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:11.5px;color:#142840;line-height:1.5;">Best historical performers shown first</div>
    </div>
  </div>

  <div style="font-family:'Space Grotesk',sans-serif;font-size:14px;color:#0b1d2e;max-width:420px;margin:0 auto;line-height:1.85;">
    Set thresholds · Click <b style="color:#22c55e;">Find TP Hitters</b><br/>
    Only stocks with evidence of hitting TP appear.
  </div>
</div>""", unsafe_allow_html=True)
        return

    # ── Render ────────────────────────────────────────────────────────────────
    summary_banner(df, min_tp1, min_tp2)

    t_cards, t_table, t_pnl, t_exp = st.tabs([
        "🎯  TP Hitter Cards", "📋  Full Table", "💰  P&L", "⬇  Export"
    ])

    # ── CARDS ─────────────────────────────────────────────────────────────────
    with t_cards:
        pc1, pc2, _ = st.columns([1.5, 1.5, 5])
        with pc1: capital  = st.number_input("Capital (₹)",        value=100000, step=10000, min_value=1000)
        with pc2: risk_pct = st.number_input("Risk per trade (%)", value=1.0, step=0.25, min_value=0.25, max_value=5.0)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        ncols = 3
        for ri in range(math.ceil(len(df) / ncols)):
            cols = st.columns(ncols)
            for ci in range(ncols):
                idx = ri * ncols + ci
                if idx >= len(df): break
                row = df.iloc[idx]
                with cols[ci]:
                    st.markdown(signal_card(row), unsafe_allow_html=True)
                    with st.expander(f"🔍  Calculator — {row['ticker']}", expanded=False):
                        icon, ocol, olbl = OUTCOME_DISP.get(row["outcome"], OUTCOME_DISP["LIVE"])
                        d   = int(row["days"])
                        d_s = f"{d} day{'s' if d!=1 else ''}" if row["outcome"] not in ("RUNNING","LIVE") else "Not yet resolved"
                        rp  = row["entry"] - row["sl"]
                        qty = max(1, int((capital*(risk_pct/100))/rp)) if rp>0 else 1
                        act_pnl = (
                            qty*(row["tp2"]-row["entry"]) if row["outcome"]=="TP2" else
                            qty*(row["tp1"]-row["entry"]) if row["outcome"]=="TP1" else
                            -qty*rp                        if row["outcome"]=="SL"  else 0.0
                        )
                        pc_col = "#22c55e" if act_pnl>0 else ("#ef4444" if act_pnl<0 else "#a78bfa")
                        st.markdown(f"""
<div style="padding:8px 2px 4px;">
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px;margin-bottom:8px;">
    <div style="background:#050f1c;border-top:2px solid {ocol};border:1px solid {ocol}18;border-radius:8px;padding:10px;">
      <div style="font-size:16px;margin-bottom:4px;">{icon}</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:700;color:{ocol};">{olbl}</div>
    </div>
    <div style="background:#050f1c;border:1px solid #0b1d2e;border-radius:8px;padding:10px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142840;margin-bottom:3px;">STATUS</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;color:#d6ecff;">{d_s}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#142840;">exit @ {fmt(row["exit_price"])}</div>
    </div>
    <div style="background:#050f1c;border:1px solid #0b1d2e;border-radius:8px;padding:10px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142840;margin-bottom:3px;">P&L {qty} shs</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700;color:{pc_col};">{fmt(act_pnl)}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
                        st.markdown(pos_calc(row["entry"],row["sl"],row["tp1"],row["tp2"],capital,risk_pct), unsafe_allow_html=True)
                    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ── TABLE ─────────────────────────────────────────────────────────────────
    with t_table:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#142840;margin-bottom:8px;">ALL QUALIFYING SIGNALS — SORTED BY HISTORICAL TP2 RATE</p>', unsafe_allow_html=True)
        tbl = df[["ticker","hist_tp2_rate","hist_tp1_rate","hist_sl_rate","hist_signals",
                  "outcome","days","entry","sl","tp1","tp2","risk_pct","gap_pct"]].copy()
        tbl.columns = ["Ticker","Hist TP2%","Hist TP1%","Hist SL%","Past Sigs",
                       "Outcome","Days","Entry","SL","TP1","TP2","Risk%","SMA Gap%"]
        st.dataframe(
            tbl.style
            .applymap(lambda v: "color:#22c55e;font-weight:700;" if v>=60 else ("color:#f59e0b;" if v>=45 else "color:#ef4444;"), subset=["Hist TP2%"])
            .applymap(lambda v: "color:#22c55e;font-weight:700;" if v>=75 else ("color:#f59e0b;" if v>=60 else "color:#ef4444;"), subset=["Hist TP1%"])
            .applymap(lambda v: "color:#22c55e;" if v<=15 else ("color:#f59e0b;" if v<=25 else "color:#ef4444;"), subset=["Hist SL%"])
            .applymap(lambda v: "color:#22c55e;font-weight:700;" if v=="TP2" else
                      ("color:#f59e0b;font-weight:700;" if v=="TP1" else
                       ("color:#ef4444;font-weight:700;" if v=="SL" else "color:#38bdf8;")), subset=["Outcome"])
            .format({"Entry":"₹{:.2f}","SL":"₹{:.2f}","TP1":"₹{:.2f}","TP2":"₹{:.2f}","Risk%":"{:.2f}%","Hist TP2%":"{:.1f}","Hist TP1%":"{:.1f}","Hist SL%":"{:.1f}"}),
            use_container_width=True, height=460,
        )

    # ── P&L ───────────────────────────────────────────────────────────────────
    with t_pnl:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#142840;margin-bottom:10px;">HYPOTHETICAL P&L · NOT GUARANTEED FUTURE RETURNS</p>', unsafe_allow_html=True)
        pa, pb, _ = st.columns([1.5, 1.5, 5])
        with pa: pcap  = st.number_input("Capital (₹)  ",        value=100000, step=10000, min_value=1000)
        with pb: prisk = st.number_input("Risk per trade (%)  ", value=1.0, step=0.25, min_value=0.25, max_value=5.0)

        risk_amt = pcap * (prisk/100)
        rows = []
        for _, row in df.iterrows():
            rp = row.entry - row.sl
            if rp <= 0: continue
            qty = max(1, int(risk_amt/rp))
            out = row.outcome
            if   out=="TP2": pnl,tag = qty*(row.tp2-row.entry), "TP2 🎯"
            elif out=="TP1": pnl,tag = qty*(row.tp1-row.entry), "TP1 ✅"
            elif out=="SL":  pnl,tag = -qty*rp,                 "SL 🛑"
            else:            pnl,tag = 0.0,                      "LIVE ⏳"
            rows.append({"Ticker":row.ticker,"Outcome":tag,"Days":int(row.days),
                         "Qty":qty,"Entry":fmt(row.entry),"Exit":fmt(row.exit_price),
                         "Hist TP2%":f"{row.hist_tp2_rate:.0f}%",
                         "P&L (₹)":round(pnl,2)})

        if not rows:
            st.info("No trades to show."); 
        else:
            pdf  = pd.DataFrame(rows)
            tot  = pdf["P&L (₹)"].sum()
            w    = (pdf["P&L (₹)"]>0).sum()
            l    = (pdf["P&L (₹)"]<0).sum()
            wr   = w/(w+l)*100 if (w+l)>0 else 0

            m = st.columns(4)
            m[0].metric("TOTAL P&L",   fmt(tot),    f"{'▲' if tot>=0 else '▼'} real outcomes")
            m[1].metric("WIN RATE",    f"{wr:.1f}%", f"{w}W / {l}L")
            m[2].metric("RISK/TRADE",  fmt(risk_amt),f"{prisk}% of capital")
            m[3].metric("SIGNALS",     len(df),      "history-verified")

            st.dataframe(
                pdf.style
                .applymap(lambda v: "color:#22c55e;" if v>0 else ("color:#ef4444;" if v<0 else "color:#a78bfa;"), subset=["P&L (₹)"])
                .applymap(lambda v: "color:#22c55e;" if "🎯" in str(v) or "✅" in str(v) else ("color:#ef4444;" if "🛑" in str(v) else "color:#a78bfa;"), subset=["Outcome"])
                .format({"P&L (₹)": "{:,.2f}"}),
                use_container_width=True, height=380,
            )
            buf = io.StringIO(); pdf.to_csv(buf, index=False)
            st.download_button("⬇  Download P&L CSV", data=buf.getvalue().encode("utf-8-sig"),
                               file_name=f"arthsutra_tphitters_{date.today()}.csv",
                               mime="text/csv", use_container_width=True)

    # ── EXPORT ────────────────────────────────────────────────────────────────
    with t_exp:
        st.dataframe(df, use_container_width=True, height=300)
        buf = io.StringIO(); df.to_csv(buf, index=False)
        st.download_button(f"⬇  Download CSV — {len(df)} TP hitters · {st.session_state['scan_done']}",
                           data=buf.getvalue().encode("utf-8-sig"),
                           file_name=f"arthsutra_tphitters_{st.session_state['scan_done']}.csv",
                           mime="text/csv", use_container_width=True)

    st.markdown(f"""
<hr/>
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;padding:3px 0;">
  <div style="display:flex;align-items:center;gap:9px;">
    <span>🎯</span>
    <div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:13px;font-weight:800;color:#0b1d2e;">Arthsutra · Only TP Hitters</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#050f1c;">SMA44/200 · PINE SCRIPT · HISTORY VERIFIED · NOT SEBI REGISTERED</div>
    </div>
  </div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:7px;color:#050f1c;">© {date.today().year} ARTHSUTRA · EDUCATIONAL USE ONLY</div>
</div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
