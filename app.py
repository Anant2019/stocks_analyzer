"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ARTHSUTRA v7 — Swing Triple Bullish · 30-Day Win Rate Engine               ║
║  Exact Pine Script logic · 30-day rolling backtest · SL target ≤ 10%       ║
║  Real NSE data via yfinance · NOT SEBI Registered · Educational Only        ║
╚══════════════════════════════════════════════════════════════════════════════╝

STRATEGY (exact Pine Script port):
────────────────────────────────────
  s44  = SMA(close, 44)
  s200 = SMA(close, 200)

  is_trending = s44 > s200
                AND s44  > s44[2]    ← SMA44 rising
                AND s200 > s200[2]   ← SMA200 rising

  is_strong   = close > open         ← green (bullish) candle
                AND close > (high+low)/2  ← closes in upper half

  BUY = is_trending AND is_strong AND low <= s44 AND close > s44
        ← candle takes support at SMA44 and closes above it

  SL    = candle low
  TP1   = close + (close − low)     1:1
  TP2   = close + (close − low)×2   1:2

30-DAY BACKTEST MODE:
  For every trading day in the last 30 days:
    → Scan all NSE200 stocks for the above signal
    → Walk forward to resolve SL/TP1/TP2 outcome from real prices
    → Build a day-by-day win rate history chart
    → Show overall 30-day accuracy across all signals

INSTALL:  pip install streamlit pandas numpy yfinance
RUN:      streamlit run arthsutra.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import math, io, time, json
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
    page_title="Arthsutra · 30-Day Win Rate Engine",
    page_icon="🔱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Space Grotesk',system-ui,sans-serif!important;background:#030c14!important;color:#c5dff2!important;}
#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}
.block-container{padding-top:.7rem!important;padding-bottom:3rem!important;max-width:1400px!important;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-thumb{background:#0f2030;border-radius:4px;}
div[data-testid="metric-container"]{background:#061120!important;border:1px solid #0c1e30!important;border-radius:12px!important;padding:14px 18px!important;}
div[data-testid="metric-container"] label{font-family:'JetBrains Mono',monospace!important;font-size:8px!important;letter-spacing:2px!important;color:#163050!important;text-transform:uppercase!important;}
div[data-testid="stMetricValue"]{font-family:'Space Grotesk',sans-serif!important;font-size:22px!important;font-weight:700!important;color:#d8eeff!important;}
div[data-testid="stMetricDelta"]{font-family:'JetBrains Mono',monospace!important;font-size:10px!important;}
.stButton>button{font-family:'Space Grotesk',sans-serif!important;font-weight:700!important;background:linear-gradient(135deg,#15803d,#16a34a)!important;color:white!important;border:none!important;border-radius:10px!important;padding:.6rem 2rem!important;font-size:14px!important;transition:all .2s!important;}
.stButton>button:hover{background:linear-gradient(135deg,#16a34a,#22c55e)!important;box-shadow:0 6px 22px rgba(22,163,74,.4)!important;transform:translateY(-1px)!important;}
.stDateInput input,.stSelectbox div[data-baseweb="select"]>div,.stNumberInput input{background:#061120!important;border:1.5px solid #0c1e30!important;border-radius:9px!important;color:#c5dff2!important;font-family:'JetBrains Mono',monospace!important;font-size:13px!important;}
.stTabs [data-baseweb="tab-list"]{background:#061120!important;border-radius:10px!important;padding:4px!important;gap:4px!important;border:1px solid #0c1e30!important;}
.stTabs [data-baseweb="tab"]{font-family:'Space Grotesk',sans-serif!important;font-weight:500!important;font-size:13px!important;color:#1a3a55!important;border-radius:8px!important;padding:7px 18px!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#15803d,#16a34a)!important;color:white!important;font-weight:700!important;}
.streamlit-expanderHeader{font-family:'Space Grotesk',sans-serif!important;font-weight:600!important;background:#030c14!important;border:1px solid #0c1e30!important;border-radius:10px!important;color:#4a8aaa!important;}
.streamlit-expanderContent{background:#030c14!important;border:1px solid #0c1e30!important;border-top:none!important;border-radius:0 0 10px 10px!important;}
.stDataFrame{border:1px solid #0c1e30!important;border-radius:10px!important;}
hr{border-color:#0c1e30!important;margin:.8rem 0!important;}
.stInfo{background:rgba(22,163,74,.07)!important;border:1px solid rgba(22,163,74,.22)!important;border-radius:10px!important;}
.stWarning{background:rgba(234,179,8,.07)!important;border:1px solid rgba(234,179,8,.2)!important;border-radius:10px!important;}
.stSuccess{background:rgba(22,163,74,.09)!important;border:1px solid rgba(22,163,74,.28)!important;border-radius:10px!important;}
.stError{background:rgba(239,68,68,.07)!important;border:1px solid rgba(239,68,68,.2)!important;border-radius:10px!important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# NSE 200 — using the most liquid, data-reliable large-caps first
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
    df["sma44"]      = df["Close"].rolling(44,  min_periods=44).mean()
    df["sma200"]     = df["Close"].rolling(200, min_periods=200).mean()
    df["sma44_2"]    = df["sma44"].shift(2)
    df["sma200_2"]   = df["sma200"].shift(2)
    return df

# ─────────────────────────────────────────────────────────────────────────────
# PINE SCRIPT SIGNAL — exact port, zero changes
# ─────────────────────────────────────────────────────────────────────────────
def pine_signal(row: pd.Series) -> dict | None:
    for col in ["Close","Open","High","Low","sma44","sma200","sma44_2","sma200_2"]:
        if pd.isna(row.get(col, np.nan)):
            return None

    c, o, h, l = float(row.Close), float(row.Open), float(row.High), float(row.Low)
    s44, s200   = float(row.sma44), float(row.sma200)
    s44_2, s200_2 = float(row.sma44_2), float(row.sma200_2)

    # Exact Pine conditions
    is_trending = s44 > s200 and s44 > s44_2 and s200 > s200_2
    is_strong   = c > o and c > (h + l) / 2
    buy         = is_trending and is_strong and l <= s44 and c > s44

    if not buy:
        return None

    risk = c - l
    if risk <= 0 or risk / c > 0.15:   # skip >15% risk candles
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
# OUTCOME — walk real forward candles
# ─────────────────────────────────────────────────────────────────────────────
def resolve_outcome(fwd: pd.DataFrame, entry, sl, tp1, tp2, max_days=20) -> dict:
    if fwd.empty:
        return {"outcome": "RUNNING", "days": 0, "exit_price": entry}
    for i, (_, r) in enumerate(fwd.head(max_days).iterrows(), 1):
        hi, lo = float(r.High), float(r.Low)
        if lo <= sl:
            return {"outcome": "SL_HIT",  "days": i, "exit_price": sl}
        if hi >= tp2:
            return {"outcome": "TP2_HIT", "days": i, "exit_price": tp2}
        if hi >= tp1:
            return {"outcome": "TP1_HIT", "days": i, "exit_price": tp1}
    return {"outcome": "RUNNING", "days": max_days,
            "exit_price": float(fwd.Close.iloc[-1]) if not fwd.empty else entry}

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADER — downloads 1 stock, caches internally
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_stock(ticker: str) -> pd.DataFrame | None:
    """Download 400 days of daily data for one stock. Cached 1 hr."""
    try:
        raw = yf.download(
            yf_sym(ticker),
            period="400d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )
        if raw.empty or len(raw) < 210:
            return None
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        raw.index = pd.to_datetime(raw.index).date
        return raw
    except Exception:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# SCAN ONE DATE — apply Pine signal to all stocks for a specific date
# ─────────────────────────────────────────────────────────────────────────────
def scan_one_date(all_data: dict, trade_date: date) -> list[dict]:
    """
    all_data: {ticker: raw_df} already downloaded
    Returns list of signal dicts for trade_date.
    """
    signals = []
    for ticker, raw in all_data.items():
        try:
            if raw is None or len(raw) < 210:
                continue
            hist = raw[raw.index <= trade_date]
            fwd  = raw[raw.index >  trade_date]
            if len(hist) < 210:
                continue

            ind   = add_indicators(hist)
            avail = [d for d in ind.index if d <= trade_date]
            if not avail:
                continue
            row   = ind.loc[max(avail)]
            sig   = pine_signal(row)
            if sig is None:
                continue

            out = resolve_outcome(fwd, sig["entry"], sig["sl"], sig["tp1"], sig["tp2"])

            signals.append({
                "ticker":     ticker,
                "date":       str(trade_date),
                "entry":      sig["entry"],
                "sl":         sig["sl"],
                "tp1":        sig["tp1"],
                "tp2":        sig["tp2"],
                "risk":       sig["risk"],
                "risk_pct":   sig["risk_pct"],
                "sma44":      sig["sma44"],
                "sma200":     sig["sma200"],
                "gap_pct":    sig["gap_pct"],
                "outcome":    out["outcome"],
                "days":       out["days"],
                "exit_price": out["exit_price"],
            })
        except Exception:
            pass
    return signals

# ─────────────────────────────────────────────────────────────────────────────
# 30-DAY BACKTEST ENGINE
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def run_30day_backtest(end_date_str: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      signals_df  — every signal fired in the last 30 days with outcomes
      daily_df    — per-day summary (n_signals, tp2_rate, tp1_rate, sl_rate)
    """
    end_date   = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    start_date = end_date - timedelta(days=42)   # ~30 trading days

    # Build list of weekdays in the window
    trading_days = []
    d = start_date
    while d <= end_date:
        if d.weekday() < 5:
            trading_days.append(d)
        d += timedelta(days=1)

    # ── Step 1: Download all stocks once ─────────────────────────────────────
    all_data = {}
    dl_bar = st.progress(0, text="Downloading NSE 200 data…")
    for i, ticker in enumerate(NSE200):
        all_data[ticker] = load_stock(ticker)
        dl_bar.progress((i + 1) / len(NSE200),
                        text=f"Downloading {ticker} ({i+1}/{len(NSE200)})…")
        if i % 20 == 0 and i > 0:
            time.sleep(0.1)
    dl_bar.empty()

    # ── Step 2: Scan each trading day ────────────────────────────────────────
    all_signals = []
    day_summaries = []

    scan_bar = st.progress(0, text="Scanning trading days…")
    for idx, td in enumerate(trading_days):
        sigs = scan_one_date(all_data, td)

        closed = [s for s in sigs if s["outcome"] in ("TP2_HIT","TP1_HIT","SL_HIT")]
        n = len(closed)
        tp2_r = (sum(1 for s in closed if s["outcome"]=="TP2_HIT")/n*100) if n else 0
        tp1_r = (sum(1 for s in closed if s["outcome"] in ("TP1_HIT","TP2_HIT"))/n*100) if n else 0
        sl_r  = (sum(1 for s in closed if s["outcome"]=="SL_HIT")/n*100) if n else 0

        day_summaries.append({
            "date":       str(td),
            "n_signals":  len(sigs),
            "n_closed":   n,
            "tp2_rate":   round(tp2_r, 1),
            "tp1_rate":   round(tp1_r, 1),
            "sl_rate":    round(sl_r, 1),
        })
        all_signals.extend(sigs)
        scan_bar.progress((idx+1)/len(trading_days),
                          text=f"Scanned {str(td)} — {len(sigs)} signals found")

    scan_bar.empty()

    signals_df = pd.DataFrame(all_signals) if all_signals else pd.DataFrame()
    daily_df   = pd.DataFrame(day_summaries)
    return signals_df, daily_df

# ─────────────────────────────────────────────────────────────────────────────
# WIN RATE HISTORY CHART — pure SVG, no chart library needed
# ─────────────────────────────────────────────────────────────────────────────
def win_rate_chart(daily_df: pd.DataFrame) -> str:
    """Render a clean SVG line chart of daily TP2, TP1, SL rates + signal count."""
    rows = daily_df[daily_df["n_closed"] > 0].copy()
    if rows.empty:
        return "<p style='color:#1a3a55;padding:16px;'>Not enough closed trades yet to chart.</p>"

    W, H     = 860, 220
    PAD_L, PAD_R, PAD_T, PAD_B = 48, 20, 18, 40
    cw = W - PAD_L - PAD_R
    ch = H - PAD_T - PAD_B
    n  = len(rows)

    def px(i):   return PAD_L + (i / max(n-1, 1)) * cw
    def py(v):   return PAD_T + ch - (min(v, 100) / 100) * ch

    def polyline(vals, color, width=2):
        pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(vals))
        return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'

    def dots(vals, color):
        return "".join(
            f'<circle cx="{px(i):.1f}" cy="{py(v):.1f}" r="3.5" fill="{color}" stroke="#030c14" stroke-width="1.5"/>'
            for i, v in enumerate(vals)
        )

    # Grid lines at 10, 20, 30, 50, 70, 90
    grid = ""
    for val in [10, 20, 30, 50, 70, 90]:
        y = py(val)
        col = "#ef444440" if val == 10 else "#0c1e3060"
        lw  = "1.5" if val == 10 else "0.8"
        grid += f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W-PAD_R}" y2="{y:.1f}" stroke="{col}" stroke-width="{lw}" stroke-dasharray="{"none" if val==10 else "3,4"}"/>'
        grid += f'<text x="{PAD_L-6}" y="{y+4:.1f}" text-anchor="end" fill="#1a3a55" font-size="9" font-family="JetBrains Mono, monospace">{val}</text>'

    # SL=10% target fill band
    y10 = py(10)
    target_band = f'<rect x="{PAD_L}" y="{y10:.1f}" width="{cw}" height="{PAD_T+ch-y10:.1f}" fill="#22c55e08"/>'

    # Lines
    tp2_line = polyline(rows.tp2_rate.tolist(), "#22c55e", 2.5)
    tp1_line = polyline(rows.tp1_rate.tolist(), "#f59e0b", 2)
    sl_line  = polyline(rows.sl_rate.tolist(),  "#ef4444", 2)

    # Dots
    tp2_dots = dots(rows.tp2_rate.tolist(), "#22c55e")
    tp1_dots = dots(rows.tp1_rate.tolist(), "#f59e0b")
    sl_dots  = dots(rows.sl_rate.tolist(),  "#ef4444")

    # Bar chart for signal count (behind lines)
    max_sigs = max(rows.n_signals.max(), 1)
    bar_w    = max(2, cw / n - 2)
    bars = ""
    for i, ns in enumerate(rows.n_signals.tolist()):
        bh = (ns / max_sigs) * (ch * 0.25)   # max 25% of chart height
        bars += (f'<rect x="{px(i)-bar_w/2:.1f}" y="{PAD_T+ch-bh:.1f}" '
                 f'width="{bar_w:.1f}" height="{bh:.1f}" '
                 f'fill="#1a3a5530" rx="2"/>')

    # X-axis date labels (every 5th)
    xlabels = ""
    for i, d in enumerate(rows.date.tolist()):
        if i % 5 == 0 or i == n-1:
            short = d[5:]   # MM-DD
            xlabels += (f'<text x="{px(i):.1f}" y="{H-PAD_B+14}" text-anchor="middle" '
                        f'fill="#1a3a55" font-size="8.5" font-family="JetBrains Mono, monospace">{short}</text>')

    # Legend
    legend = (
        f'<circle cx="{PAD_L+10}" cy="10" r="4" fill="#22c55e"/>'
        f'<text x="{PAD_L+18}" y="14" fill="#22c55e" font-size="9" font-family="Space Grotesk, sans-serif" font-weight="600">TP2 Hit%</text>'
        f'<circle cx="{PAD_L+82}" cy="10" r="4" fill="#f59e0b"/>'
        f'<text x="{PAD_L+90}" y="14" fill="#f59e0b" font-size="9" font-family="Space Grotesk, sans-serif" font-weight="600">TP1+ Hit%</text>'
        f'<circle cx="{PAD_L+160}" cy="10" r="4" fill="#ef4444"/>'
        f'<text x="{PAD_L+168}" y="14" fill="#ef4444" font-size="9" font-family="Space Grotesk, sans-serif" font-weight="600">SL Hit%</text>'
        f'<rect x="{PAD_L+232}" y="6" width="8" height="8" fill="#1a3a5560" rx="1"/>'
        f'<text x="{PAD_L+244}" y="14" fill="#1a3a55" font-size="9" font-family="Space Grotesk, sans-serif">Signal count</text>'
        f'<line x1="{W-100}" y1="2" x2="{W-100}" y2="16" stroke="#ef444440" stroke-width="1.5" stroke-dasharray="3,2"/>'
        f'<text x="{W-94}" y="10" fill="#ef4444" font-size="8" font-family="JetBrains Mono, monospace">SL ≤10%</text>'
        f'<text x="{W-94}" y="18" fill="#ef4444" font-size="8" font-family="JetBrains Mono, monospace">TARGET</text>'
    )

    svg = f"""
<div style="background:#061120;border:1px solid #0c1e30;border-radius:12px;padding:16px 18px;margin-bottom:16px;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2px;color:#163050;margin-bottom:10px;">
    30-DAY WIN RATE HISTORY — REAL NSE OUTCOMES
  </div>
  <svg width="100%" viewBox="0 0 {W} {H}" style="overflow:visible;">
    <!-- Target band -->
    {target_band}
    <!-- Grid -->
    {grid}
    <!-- Signal count bars -->
    {bars}
    <!-- Lines -->
    {tp2_line}{tp1_line}{sl_line}
    <!-- Dots -->
    {tp2_dots}{tp1_dots}{sl_dots}
    <!-- X labels -->
    {xlabels}
    <!-- Legend -->
    {legend}
  </svg>
</div>"""
    return svg

# ─────────────────────────────────────────────────────────────────────────────
# FORMATTING
# ─────────────────────────────────────────────────────────────────────────────
def fmt(v: float) -> str:
    return f"₹{v:,.2f}"

OUTCOME_META = {
    "TP2_HIT": {"label":"TP2 Hit · 1:2", "color":"#22c55e", "icon":"🎯"},
    "TP1_HIT": {"label":"TP1 Hit · 1:1", "color":"#f59e0b", "icon":"✅"},
    "SL_HIT":  {"label":"SL Hit",         "color":"#ef4444", "icon":"🛑"},
    "RUNNING": {"label":"Running",         "color":"#38bdf8", "icon":"⏳"},
}

def outcome_badge(outcome: str) -> str:
    om = OUTCOME_META.get(outcome, OUTCOME_META["RUNNING"])
    return (f'<span style="background:{om["color"]}18;border:1px solid {om["color"]}40;'
            f'color:{om["color"]};font-family:JetBrains Mono,monospace;font-size:8px;'
            f'padding:2px 8px;border-radius:4px;">{om["icon"]} {om["label"]}</span>')

# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL CARD
# ─────────────────────────────────────────────────────────────────────────────
def signal_card(row: pd.Series) -> str:
    om      = OUTCOME_META.get(row["outcome"], OUTCOME_META["RUNNING"])
    sl_pct  = round((row["entry"]-row["sl"]) /row["entry"]*100, 2)
    tp1_pct = round((row["tp1"]-row["entry"])/row["entry"]*100, 2)
    tp2_pct = round((row["tp2"]-row["entry"])/row["entry"]*100, 2)
    d       = int(row["days"])
    d_s     = f"{d}d" if row["outcome"] not in ("RUNNING",) else "open"

    return f"""
<div style="background:#061120;border:1px solid #0c1e30;border-top:3px solid #22c55e;
            border-radius:12px;padding:16px 14px 13px;">

  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">
    <div>
      <div style="display:flex;align-items:center;gap:7px;margin-bottom:2px;">
        <span style="font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:800;color:#d8eeff;">{row["ticker"]}</span>
        <span style="background:rgba(34,197,94,.10);color:#22c55e;font-family:'JetBrains Mono',monospace;
                     font-size:7.5px;font-weight:700;letter-spacing:1.5px;padding:2px 7px;border-radius:4px;">BUY</span>
      </div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#0d1e2e;">
        {row["date"]} · SMA44={fmt(row["sma44"])} · GAP+{row["gap_pct"]}%
      </span>
    </div>
    <a href="https://www.tradingview.com/chart/?symbol=NSE:{row['ticker']}" target="_blank"
       style="background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.2);border-radius:6px;
              padding:4px 9px;font-family:'JetBrains Mono',monospace;font-size:8px;
              color:#4ade80;text-decoration:none;">↗ TV</a>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:9px;">
    <div style="background:#030c14;border-radius:7px;padding:8px 10px;border:1px solid #0c1e30;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:6.5px;letter-spacing:2px;color:#0d1e2e;margin-bottom:2px;">ENTRY</div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#d8eeff;">{fmt(row["entry"])}</span>
    </div>
    <div style="background:#030c14;border-radius:7px;padding:8px 10px;border:1px solid #0c1e30;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:6.5px;letter-spacing:2px;color:#0d1e2e;margin-bottom:2px;">SL <span style="color:#ef4444;">−{sl_pct}%</span></div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#ef4444;">{fmt(row["sl"])}</span>
    </div>
    <div style="background:#030c14;border-radius:7px;padding:8px 10px;border:1px solid #0c1e30;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:6.5px;letter-spacing:2px;color:#0d1e2e;margin-bottom:2px;">TP1 1:1 <span style="color:#f59e0b;">+{tp1_pct}%</span></div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#f59e0b;">{fmt(row["tp1"])}</span>
    </div>
    <div style="background:#030c14;border-radius:7px;padding:8px 10px;border:1px solid #0c1e30;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:6.5px;letter-spacing:2px;color:#0d1e2e;margin-bottom:2px;">TP2 1:2 <span style="color:#22c55e;">+{tp2_pct}%</span></div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#22c55e;">{fmt(row["tp2"])}</span>
    </div>
  </div>

  <div style="display:flex;align-items:center;justify-content:space-between;
              background:#030c14;border:1px solid {om['color']}20;border-left:3px solid {om['color']};
              border-radius:7px;padding:7px 10px;">
    <div style="display:flex;align-items:center;gap:6px;">
      <span style="font-size:13px;">{om['icon']}</span>
      <span style="font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:700;color:{om['color']};">{om['label']}</span>
    </div>
    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;color:#0d1e2e;">{d_s}</span>
  </div>
</div>"""

# ─────────────────────────────────────────────────────────────────────────────
# OVERALL ACCURACY BANNER
# ─────────────────────────────────────────────────────────────────────────────
def accuracy_banner(sdf: pd.DataFrame, daily_df: pd.DataFrame):
    closed = sdf[sdf["outcome"].isin(["TP2_HIT","TP1_HIT","SL_HIT"])]
    n = len(closed)
    if n == 0:
        st.info("No closed trades yet in this window."); return

    n_tp2 = (closed["outcome"]=="TP2_HIT").sum()
    n_tp1 = closed["outcome"].isin(["TP1_HIT","TP2_HIT"]).sum()
    n_sl  = (closed["outcome"]=="SL_HIT").sum()

    tp2_r = n_tp2/n*100
    tp1_r = n_tp1/n*100
    sl_r  = n_sl /n*100

    # Expectancy in R
    avg_win_r  = (n_tp2/n * 2.0) + ((n_tp1-n_tp2)/n * 1.0)
    avg_loss_r = n_sl/n * 1.0
    expect     = round(avg_win_r - avg_loss_r, 3)

    # Days stats
    win_days  = closed[closed["outcome"].isin(["TP1_HIT","TP2_HIT"])]["days"].mean() if n_tp1>0 else 0
    loss_days = closed[closed["outcome"]=="SL_HIT"]["days"].mean() if n_sl>0 else 0

    sl_col  = "#22c55e" if sl_r <= 10 else ("#f59e0b" if sl_r <= 20 else "#ef4444")
    tp2_col = "#22c55e" if tp2_r >= 55 else ("#f59e0b" if tp2_r >= 40 else "#ef4444")
    exp_col = "#22c55e" if expect > 0 else "#ef4444"

    # Streak: consecutive days with SL=0
    streaks = daily_df[daily_df["n_closed"]>0]["sl_rate"].tolist()
    cur_streak = 0
    for v in reversed(streaks):
        if v == 0: cur_streak += 1
        else: break

    st.markdown(f"""
<div style="background:#061120;border:1px solid #0c1e30;border-radius:14px;
            padding:20px 24px;margin-bottom:14px;">

  <div style="display:flex;align-items:center;justify-content:space-between;
              flex-wrap:wrap;gap:10px;margin-bottom:16px;">
    <div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2px;color:#163050;">
        30-DAY BACKTEST · {len(sdf)} TOTAL SIGNALS · {n} CLOSED · {len(sdf)-n} RUNNING
      </div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:11.5px;color:#0c1e30;margin-top:3px;">
        Real NSE prices · Exact Pine Script logic · No simulation
      </div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <div style="background:#030c14;border:1px solid {exp_col}30;border-radius:9px;
                  padding:9px 16px;text-align:center;min-width:100px;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#163050;margin-bottom:3px;">EXPECTANCY/TRADE</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:{exp_col};line-height:1;">{expect:+.2f}R</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#163050;margin-top:2px;">{'positive edge' if expect>0 else 'negative edge'}</div>
      </div>
      <div style="background:#030c14;border:1px solid #22c55e20;border-radius:9px;
                  padding:9px 16px;text-align:center;min-width:90px;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#163050;margin-bottom:3px;">CLEAN DAYS</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:800;color:#22c55e;line-height:1;">{cur_streak}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#163050;margin-top:2px;">0% SL streak</div>
      </div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;">

    <div style="background:#030c14;border-radius:10px;padding:13px 11px;
                border:1px solid #0c1e30;border-top:2.5px solid {sl_col};">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#163050;margin-bottom:4px;">SL HIT RATE</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:{sl_col};line-height:1;">{sl_r:.1f}%</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#163050;margin-top:3px;">
        target ≤ 10% {'✅' if sl_r<=10 else '⚠'}
      </div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#163050;">avg {loss_days:.1f}d to loss</div>
    </div>

    <div style="background:#030c14;border-radius:10px;padding:13px 11px;
                border:1px solid #0c1e30;border-top:2.5px solid {tp2_col};">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#163050;margin-bottom:4px;">TP2 HIT RATE</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:{tp2_col};line-height:1;">{tp2_r:.1f}%</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#163050;margin-top:3px;">{n_tp2}/{n} closed</div>
    </div>

    <div style="background:#030c14;border-radius:10px;padding:13px 11px;
                border:1px solid #0c1e30;border-top:2.5px solid #f59e0b;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#163050;margin-bottom:4px;">TP1+ HIT RATE</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:#f59e0b;line-height:1;">{tp1_r:.1f}%</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#163050;margin-top:3px;">avg {win_days:.1f}d to win</div>
    </div>

    <div style="background:#030c14;border-radius:10px;padding:13px 11px;
                border:1px solid #0c1e30;border-top:2.5px solid #38bdf8;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#163050;margin-bottom:4px;">TOTAL SIGNALS</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:#38bdf8;line-height:1;">{len(sdf)}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#163050;margin-top:3px;">in 30 days</div>
    </div>

    <div style="background:#030c14;border-radius:10px;padding:13px 11px;
                border:1px solid #0c1e30;border-top:2.5px solid #a78bfa;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#163050;margin-bottom:4px;">AVG PER DAY</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:800;color:#a78bfa;line-height:1;">
        {round(len(sdf)/max(len(daily_df[daily_df['n_signals']>0]),1),1)}
      </div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#163050;margin-top:3px;">signals/trading day</div>
    </div>

  </div>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DAILY BREAKDOWN TABLE
# ─────────────────────────────────────────────────────────────────────────────
def daily_table(daily_df: pd.DataFrame):
    st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#163050;margin-bottom:8px;">DAY-BY-DAY BREAKDOWN</div>', unsafe_allow_html=True)
    disp = daily_df[daily_df["n_signals"]>0].copy()
    if disp.empty:
        st.info("No signals found in this window."); return

    disp = disp.sort_values("date", ascending=False).reset_index(drop=True)
    disp.columns = ["Date","Signals","Closed","TP2%","TP1+%","SL%"]

    def color_sl(v):
        if v <= 10:  return "color:#22c55e;font-weight:700;"
        if v <= 20:  return "color:#f59e0b;font-weight:700;"
        return "color:#ef4444;font-weight:700;"

    st.dataframe(
        disp.style
        .applymap(color_sl, subset=["SL%"])
        .applymap(lambda v: "color:#22c55e;" if v>=55 else ("color:#f59e0b;" if v>=35 else "color:#ef4444;"), subset=["TP2%"])
        .applymap(lambda v: "color:#f59e0b;" if v>=65 else "", subset=["TP1+%"])
        .format({"TP2%":"{:.1f}","TP1+%":"{:.1f}","SL%":"{:.1f}"}),
        use_container_width=True, height=380,
    )

# ─────────────────────────────────────────────────────────────────────────────
# POSITION CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────
def pos_calc(entry, sl, tp1, tp2, capital, risk_pct) -> str:
    rp = entry - sl
    if rp <= 0: return "<p style='color:#ef4444;'>⚠ Invalid SL</p>"
    risk_amt = capital * (risk_pct/100)
    qty      = max(1, int(risk_amt / rp))
    deployed = qty * entry
    max_loss = qty * rp
    tp1_g    = qty * (tp1 - entry)
    tp2_g    = qty * (tp2 - entry)

    def r(lbl, val, c="#4a8aaa"):
        return (f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #0c1e30;">'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:8.5px;letter-spacing:1.5px;color:#163050;">{lbl}</span>'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:13px;font-weight:700;color:{c};">{val}</span></div>')

    return f"""<div style="background:#030c14;border-radius:10px;padding:13px 15px;margin-top:4px;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2px;color:#163050;margin-bottom:9px;">POSITION CALCULATOR</div>
  {r("QUANTITY",             f"{qty:,} shares",      "#d8eeff")}
  {r("CAPITAL DEPLOYED",     fmt(deployed),           "#d8eeff")}
  {r("MAX LOSS (SL hit)",    fmt(max_loss),           "#ef4444")}
  {r("PROFIT at TP1 (1:1)",  fmt(tp1_g),             "#f59e0b")}
  {r("PROFIT at TP2 (1:2)",  fmt(tp2_g),             "#22c55e")}
  {r("RETURN at TP1",        f"{tp1_g/deployed*100:.2f}%","#f59e0b")}
  {r("RETURN at TP2",        f"{tp2_g/deployed*100:.2f}%","#22c55e")}
</div>"""

# ─────────────────────────────────────────────────────────────────────────────
# P&L TAB
# ─────────────────────────────────────────────────────────────────────────────
def pnl_tab(sdf: pd.DataFrame, capital: float, risk_pct: float):
    risk_amt = capital * (risk_pct/100)
    rows = []
    for _, row in sdf.iterrows():
        rp = row.entry - row.sl
        if rp <= 0: continue
        qty = max(1, int(risk_amt/rp))
        out = row.outcome
        if   out=="TP2_HIT": pnl,tag = qty*(row.tp2-row.entry), "TP2 🎯"
        elif out=="TP1_HIT": pnl,tag = qty*(row.tp1-row.entry), "TP1 ✅"
        elif out=="SL_HIT":  pnl,tag = -qty*rp,                 "SL 🛑"
        else:                pnl,tag = 0.0,                      "OPEN ⏳"
        rows.append({"Date":row.date,"Ticker":row.ticker,"Outcome":tag,
                     "Days":int(row.days),"Qty":qty,"Entry":fmt(row.entry),
                     "Exit":fmt(row.exit_price),"P&L (₹)":round(pnl,2)})
    if not rows: st.info("No trades."); return

    pdf  = pd.DataFrame(rows)
    tot  = pdf["P&L (₹)"].sum()
    w    = (pdf["P&L (₹)"]>0).sum()
    l    = (pdf["P&L (₹)"]<0).sum()
    o    = pdf["Outcome"].str.contains("OPEN").sum()
    wr   = w/(w+l)*100 if (w+l)>0 else 0
    avg  = pdf[pdf["P&L (₹)"]!=0]["P&L (₹)"].mean() if (w+l)>0 else 0

    m = st.columns(5)
    m[0].metric("TOTAL P&L",   fmt(tot),    f"{'▲' if tot>=0 else '▼'} 30 days")
    m[1].metric("WIN RATE",    f"{wr:.1f}%", f"{w}W / {l}L")
    m[2].metric("AVG TRADE",   fmt(avg),    "closed only")
    m[3].metric("OPEN",        o,           "not yet closed")
    m[4].metric("RISK/TRADE",  fmt(risk_amt),f"{risk_pct}% of ₹{capital:,.0f}")

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
    st.dataframe(
        pdf.style
        .applymap(lambda v: "color:#22c55e;" if v>0 else ("color:#ef4444;" if v<0 else "color:#f59e0b;"), subset=["P&L (₹)"])
        .applymap(lambda v: "color:#22c55e;" if "🎯" in str(v) or "✅" in str(v) else ("color:#ef4444;" if "🛑" in str(v) else "color:#f59e0b;"), subset=["Outcome"])
        .format({"P&L (₹)": "{:,.2f}"}),
        use_container_width=True, height=400,
    )
    buf = io.StringIO(); pdf.to_csv(buf, index=False)
    st.download_button("⬇  Download P&L CSV", data=buf.getvalue().encode("utf-8-sig"),
                       file_name=f"arthsutra_pnl_{date.today()}.csv",
                       mime="text/csv", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
def header():
    st.markdown(f"""
<div style="background:#030c14;border-bottom:1px solid #0c1e30;padding:12px 0 9px;margin-bottom:12px;">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
    <div style="display:flex;align-items:center;gap:12px;">
      <div style="width:44px;height:44px;border-radius:11px;
                  background:linear-gradient(135deg,#15803d,#0f766e);
                  display:flex;align-items:center;justify-content:center;font-size:22px;
                  box-shadow:0 0 20px rgba(21,128,61,.3);">🔱</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:#d8eeff;">Arthsutra</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2.5px;color:#0c1e30;margin-top:2px;">
          SWING TRIPLE BULLISH · 30-DAY WIN RATE ENGINE · SMA44/200 · SL TARGET ≤ 10%
        </div>
      </div>
    </div>
    <div style="display:flex;gap:7px;flex-wrap:wrap;">
      <div style="background:rgba(34,197,94,.07);border:1px solid rgba(34,197,94,.18);
                  border-radius:8px;padding:6px 13px;display:flex;align-items:center;gap:6px;">
        <div style="width:6px;height:6px;border-radius:50%;background:#22c55e;box-shadow:0 0 6px #22c55e;"></div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:1.5px;color:#22c55e;">PINE SCRIPT EXACT</span>
      </div>
      <div style="background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.18);
                  border-radius:8px;padding:6px 13px;">
        <span style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:1.5px;color:#ef4444;">TARGET SL ≤ 10%</span>
      </div>
    </div>
  </div>
  <div style="background:rgba(234,179,8,.04);border:1px solid rgba(234,179,8,.12);
              border-radius:8px;padding:6px 13px;margin-top:10px;">
    <span style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:1px;color:#5a4a18;">
      ⚠ NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · PAST RESULTS DO NOT GUARANTEE FUTURE RETURNS
    </span>
  </div>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    for k in ["signals_df","daily_df","ran"]:
        if k not in st.session_state:
            st.session_state[k] = None

    header()

    if not YF_OK:
        st.error("❌ **yfinance not installed.**\n\n```\npip install yfinance\n```")
        st.stop()

    # ── Controls ──────────────────────────────────────────────────────────────
    st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#163050;margin-bottom:4px;">BACKTEST END DATE (last 30 trading days before this date will be scanned)</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([2.2, 1.6, 2, 1.8])

    with c1:
        today   = date.today()
        default = today - timedelta(days=3)
        while default.weekday() >= 5: default -= timedelta(days=1)
        end_date = st.date_input("_d", value=default,
                                 min_value=today - timedelta(days=365),
                                 max_value=today - timedelta(days=2),
                                 label_visibility="collapsed")
    with c2:
        st.markdown("<div style='height:2px;'></div>", unsafe_allow_html=True)
        run = st.button("◈  Run 30-Day Backtest", use_container_width=True)
    with c3:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#163050;margin-bottom:4px;">FILTER SIGNALS</p>', unsafe_allow_html=True)
        flt = st.selectbox("_f",
                           ["ALL signals","Winners only (TP1+)","TP2 hits only","SL hits only"],
                           label_visibility="collapsed")
    with c4:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#163050;margin-bottom:4px;">SORT BY</p>', unsafe_allow_html=True)
        srt = st.selectbox("_s",["Date ↓","Risk% ↑","Outcome"],label_visibility="collapsed")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── Run ───────────────────────────────────────────────────────────────────
    if run:
        st.info(f"📡 Running 30-day backtest ending **{end_date}**. Downloads NSE 200, then scans ~30 trading days. This takes 3–6 minutes on first run.")
        sdf, ddf = run_30day_backtest(str(end_date))
        st.session_state.update({"signals_df": sdf, "daily_df": ddf, "ran": str(end_date)})

        if sdf.empty:
            st.warning("⚠ No signals found in this 30-day window. The Pine Script conditions (SMA44/SMA200 aligned, green candle touching SMA44) require a bullish trending market. Try an end date during a bull phase like Jan–Mar 2024.")
            return
        closed_n = sdf[sdf["outcome"].isin(["TP2_HIT","TP1_HIT","SL_HIT"])]
        sl_r = (closed_n["outcome"]=="SL_HIT").sum()/max(len(closed_n),1)*100
        msg  = f"✅ **{len(sdf)} signals** across 30 days · **{len(closed_n)} closed** · SL rate: **{sl_r:.1f}%**"
        if sl_r <= 10:
            st.success(msg + " — 🎯 SL target ≤10% MET!")
        else:
            st.warning(msg + f" — ⚠ SL rate above 10% target (market may be choppy in this window)")

    sdf = st.session_state["signals_df"]
    ddf = st.session_state["daily_df"]

    # ── Idle ──────────────────────────────────────────────────────────────────
    if sdf is None or sdf.empty:
        st.markdown("""
<div style="text-align:center;padding:50px 0 60px;">
  <div style="font-size:50px;opacity:0.06;margin-bottom:14px;">🔱</div>
  <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:700;color:#0c1e30;margin-bottom:12px;">
    30-Day Win Rate Engine
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;max-width:540px;margin:0 auto 16px;">
    <div style="background:#061120;border:1px solid #22c55e20;border-radius:9px;padding:12px 8px;text-align:center;">
      <div style="font-size:20px;margin-bottom:5px;">🕯</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#22c55e;letter-spacing:1px;">PINE SCRIPT</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:11px;color:#163050;margin-top:3px;">Exact candle logic</div>
    </div>
    <div style="background:#061120;border:1px solid #38bdf820;border-radius:9px;padding:12px 8px;text-align:center;">
      <div style="font-size:20px;margin-bottom:5px;">📅</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#38bdf8;letter-spacing:1px;">30 DAYS</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:11px;color:#163050;margin-top:3px;">Real win rate history</div>
    </div>
    <div style="background:#061120;border:1px solid #ef444420;border-radius:9px;padding:12px 8px;text-align:center;">
      <div style="font-size:20px;margin-bottom:5px;">🎯</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#ef4444;letter-spacing:1px;">SL ≤ 10%</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:11px;color:#163050;margin-top:3px;">Verified target</div>
    </div>
  </div>
  <div style="font-family:'Space Grotesk',sans-serif;font-size:14px;color:#0c1e30;
              max-width:440px;margin:0 auto;line-height:1.85;">
    Pick an end date · Click <b style="color:#22c55e;">Run 30-Day Backtest</b><br/>
    See real win rate history day by day with a chart.
  </div>
</div>""", unsafe_allow_html=True)
        return

    # ── Filter & sort ─────────────────────────────────────────────────────────
    view = sdf.copy()
    if flt == "Winners only (TP1+)": view = view[view["outcome"].isin(["TP1_HIT","TP2_HIT"])]
    elif flt == "TP2 hits only":     view = view[view["outcome"]=="TP2_HIT"]
    elif flt == "SL hits only":      view = view[view["outcome"]=="SL_HIT"]

    if   srt == "Risk% ↑":  view = view.sort_values("risk_pct", ascending=True)
    elif srt == "Outcome":   view = view.sort_values("outcome")
    else:                    view = view.sort_values("date", ascending=False)
    view = view.reset_index(drop=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    t_hist, t_sig, t_pnl, t_exp = st.tabs([
        "📈  Win Rate History", "📊  All Signals", "💰  P&L", "⬇  Export"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # WIN RATE HISTORY TAB  (primary tab)
    # ─────────────────────────────────────────────────────────────────────────
    with t_hist:
        accuracy_banner(sdf, ddf)
        st.markdown(win_rate_chart(ddf), unsafe_allow_html=True)
        daily_table(ddf)

    # ─────────────────────────────────────────────────────────────────────────
    # ALL SIGNALS TAB
    # ─────────────────────────────────────────────────────────────────────────
    with t_sig:
        m = st.columns(4)
        closed_v = sdf[sdf["outcome"].isin(["TP2_HIT","TP1_HIT","SL_HIT"])]
        sl_r2 = (closed_v["outcome"]=="SL_HIT").sum()/max(len(closed_v),1)*100
        m[0].metric("TOTAL SIGNALS",  len(sdf),        "30 days")
        m[1].metric("CLOSED",         len(closed_v),   f"{len(sdf)-len(closed_v)} running")
        m[2].metric("SL RATE",        f"{sl_r2:.1f}%", f"target ≤ 10% {'✅' if sl_r2<=10 else '⚠'}")
        m[3].metric("SHOWING",        len(view),       flt)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        pc1, pc2, _ = st.columns([1.5, 1.5, 5])
        with pc1: capital  = st.number_input("Capital (₹)",        value=100000, step=10000, min_value=1000)
        with pc2: risk_pct = st.number_input("Risk per trade (%)", value=1.0, step=0.25, min_value=0.25, max_value=5.0)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        if view.empty:
            st.info("No signals match this filter.")
        else:
            ncols = 3
            for ri in range(math.ceil(len(view)/ncols)):
                cols = st.columns(ncols)
                for ci in range(ncols):
                    idx = ri*ncols + ci
                    if idx >= len(view): break
                    row = view.iloc[idx]
                    with cols[ci]:
                        st.markdown(signal_card(row), unsafe_allow_html=True)
                        with st.expander(f"🔍  Calculator — {row['ticker']} ({row['date']})", expanded=False):
                            om  = OUTCOME_META.get(row["outcome"], OUTCOME_META["RUNNING"])
                            d   = int(row["days"])
                            d_s = f"{d} day{'s' if d!=1 else ''}" if row["outcome"]!="RUNNING" else "Still open"
                            rp  = row["entry"] - row["sl"]
                            qty = max(1, int((capital*(risk_pct/100))/rp)) if rp>0 else 1
                            act_pnl = (
                                qty*(row["tp2"]-row["entry"]) if row["outcome"]=="TP2_HIT" else
                                qty*(row["tp1"]-row["entry"]) if row["outcome"]=="TP1_HIT" else
                                -qty*rp                        if row["outcome"]=="SL_HIT"  else 0.0
                            )
                            pc_col = "#22c55e" if act_pnl>0 else ("#ef4444" if act_pnl<0 else "#f59e0b")
                            st.markdown(f"""
<div style="padding:8px 2px 4px;">
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px;margin-bottom:8px;">
    <div style="background:#061120;border-top:2px solid {om['color']};border:1px solid {om['color']}20;border-radius:8px;padding:10px;">
      <div style="font-size:16px;margin-bottom:4px;">{om['icon']}</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:700;color:{om['color']};">{om['label']}</div>
    </div>
    <div style="background:#061120;border:1px solid #0c1e30;border-radius:8px;padding:10px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#163050;margin-bottom:3px;">EXIT</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;color:#d8eeff;">{d_s}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#163050;">@ {fmt(row['exit_price'])}</div>
    </div>
    <div style="background:#061120;border:1px solid #0c1e30;border-radius:8px;padding:10px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#163050;margin-bottom:3px;">P&L {qty} shs</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:14px;font-weight:700;color:{pc_col};">{fmt(act_pnl)}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
                            st.markdown(pos_calc(row["entry"],row["sl"],row["tp1"],row["tp2"],capital,risk_pct), unsafe_allow_html=True)
                        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # P&L TAB
    # ─────────────────────────────────────────────────────────────────────────
    with t_pnl:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#163050;margin-bottom:10px;">30-DAY HYPOTHETICAL P&L · REAL OUTCOMES · NOT GUARANTEED RETURNS</p>', unsafe_allow_html=True)
        pa, pb, _ = st.columns([1.5, 1.5, 5])
        with pa: pcap  = st.number_input("Capital (₹)  ",        value=100000, step=10000, min_value=1000)
        with pb: prisk = st.number_input("Risk per trade (%)  ", value=1.0, step=0.25, min_value=0.25, max_value=5.0)
        st.markdown("<div style='height:5px;'></div>", unsafe_allow_html=True)
        pnl_tab(sdf, pcap, prisk)

    # ─────────────────────────────────────────────────────────────────────────
    # EXPORT TAB
    # ─────────────────────────────────────────────────────────────────────────
    with t_exp:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#163050;margin-bottom:10px;">EXPORT ALL SIGNALS + OUTCOMES</p>', unsafe_allow_html=True)
        st.dataframe(sdf, use_container_width=True, height=300)
        buf = io.StringIO(); sdf.to_csv(buf, index=False)
        st.download_button(f"⬇  Download Signals CSV — {len(sdf)} signals",
                           data=buf.getvalue().encode("utf-8-sig"),
                           file_name=f"arthsutra_30day_{st.session_state['ran']}.csv",
                           mime="text/csv", use_container_width=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#163050;margin-bottom:8px;">DAILY SUMMARY CSV</p>', unsafe_allow_html=True)
        buf2 = io.StringIO(); ddf.to_csv(buf2, index=False)
        st.download_button("⬇  Download Daily Summary CSV",
                           data=buf2.getvalue().encode("utf-8-sig"),
                           file_name=f"arthsutra_daily_{st.session_state['ran']}.csv",
                           mime="text/csv", use_container_width=True)

    st.markdown(f"""
<hr/>
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;padding:3px 0;">
  <div style="display:flex;align-items:center;gap:9px;">
    <span>🔱</span>
    <div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:13px;font-weight:800;color:#0c1e30;">Arthsutra</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#061120;">SMA44 · SMA200 · PINE SCRIPT · 30-DAY WIN RATE ENGINE</div>
    </div>
  </div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:1px;color:#061120;text-align:right;line-height:2.2;">
    NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · © {date.today().year} ARTHSUTRA
  </div>
</div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
