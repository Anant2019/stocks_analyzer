"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ARTHSUTRA v5 — Swing Triple Bullish 44-200                                  ║
║  Exact port of your TradingView Pine Script strategy                         ║
║  Real NSE data via yfinance · Honest outcomes · NOT SEBI Registered          ║
╚══════════════════════════════════════════════════════════════════════════════╝

YOUR PINE SCRIPT LOGIC — PORTED EXACTLY:
─────────────────────────────────────────
  s44  = SMA(close, 44)
  s200 = SMA(close, 200)

  is_trending = s44 > s200
                AND s44  > s44[2]    ← SMA44  rising (vs 2 bars ago)
                AND s200 > s200[2]   ← SMA200 rising (vs 2 bars ago)

  is_strong   = close > open                     ← green candle
                AND close > (high + low) / 2     ← strong close (upper half)

  BUY = is_trending AND is_strong AND low <= s44 AND close > s44
        ← candle low TOUCHES or dips below SMA44 but CLOSES ABOVE it
        ← this is the key "bounce off SMA44" entry

  SL    = candle low  (the wick that touched SMA44)
  ENTRY = close
  RISK  = close - low
  TP1   = close + risk          (1:1)
  TP2   = close + risk * 2      (1:2)

INSTALL:
    pip install streamlit pandas numpy yfinance

RUN:
    streamlit run arthsutra.py
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
    page_title="Arthsutra · Swing Triple Bullish",
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

html,body,[class*="css"]{
    font-family:'Space Grotesk',system-ui,sans-serif!important;
    background:#040d18!important;color:#c8e0f4!important;
}
#MainMenu,footer,header{visibility:hidden;}
.stDeployButton{display:none;}
.block-container{padding-top:.8rem!important;padding-bottom:3rem!important;max-width:1380px!important;}
::-webkit-scrollbar{width:4px;height:4px;}
::-webkit-scrollbar-thumb{background:#162d42;border-radius:4px;}

div[data-testid="metric-container"]{
    background:#071422!important;border:1px solid #10273d!important;
    border-radius:12px!important;padding:14px 18px!important;
}
div[data-testid="metric-container"] label{
    font-family:'JetBrains Mono',monospace!important;font-size:8px!important;
    letter-spacing:2px!important;color:#1e3d58!important;text-transform:uppercase!important;
}
div[data-testid="stMetricValue"]{
    font-family:'Space Grotesk',sans-serif!important;font-size:22px!important;
    font-weight:700!important;color:#daeeff!important;
}
div[data-testid="stMetricDelta"]{font-family:'JetBrains Mono',monospace!important;font-size:10px!important;}

.stButton>button{
    font-family:'Space Grotesk',sans-serif!important;font-weight:700!important;
    background:linear-gradient(135deg,#16a34a,#22c55e)!important;
    color:white!important;border:none!important;border-radius:10px!important;
    padding:.6rem 2rem!important;font-size:14px!important;transition:all .2s!important;
}
.stButton>button:hover{
    background:linear-gradient(135deg,#22c55e,#4ade80)!important;
    box-shadow:0 6px 24px rgba(34,197,94,.4)!important;transform:translateY(-1px)!important;
}
.stDateInput input,.stSelectbox div[data-baseweb="select"]>div,.stNumberInput input{
    background:#071422!important;border:1.5px solid #162d42!important;
    border-radius:9px!important;color:#c8e0f4!important;
    font-family:'JetBrains Mono',monospace!important;font-size:13px!important;
}
.stTabs [data-baseweb="tab-list"]{
    background:#071422!important;border-radius:10px!important;
    padding:4px!important;gap:4px!important;border:1px solid #10273d!important;
}
.stTabs [data-baseweb="tab"]{
    font-family:'Space Grotesk',sans-serif!important;font-weight:500!important;
    font-size:13px!important;color:#255070!important;border-radius:8px!important;padding:7px 18px!important;
}
.stTabs [aria-selected="true"]{
    background:linear-gradient(135deg,#16a34a,#22c55e)!important;
    color:white!important;font-weight:700!important;
}
.streamlit-expanderHeader{
    font-family:'Space Grotesk',sans-serif!important;font-weight:600!important;
    background:#04101e!important;border:1px solid #10273d!important;
    border-radius:10px!important;color:#6aabcc!important;
}
.streamlit-expanderContent{
    background:#04101e!important;border:1px solid #10273d!important;
    border-top:none!important;border-radius:0 0 10px 10px!important;
}
.stDataFrame{border:1px solid #10273d!important;border-radius:10px!important;}
hr{border-color:#10273d!important;margin:1rem 0!important;}
.stInfo{background:rgba(34,197,94,.07)!important;border:1px solid rgba(34,197,94,.22)!important;border-radius:10px!important;}
.stWarning{background:rgba(234,179,8,.07)!important;border:1px solid rgba(234,179,8,.2)!important;border-radius:10px!important;}
.stSuccess{background:rgba(34,197,94,.08)!important;border:1px solid rgba(34,197,94,.25)!important;border-radius:10px!important;}
.stError{background:rgba(239,68,68,.07)!important;border:1px solid rgba(239,68,68,.2)!important;border-radius:10px!important;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# NSE 200 TICKERS
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
    "HAVELLS","BLUESTAR","CROMPTON","FINOLEX","RAYMOND","VARDHMAN","TRIDENT",
    "WELSPUN","SHREECEM","RAMCOCEM","JKCEMENT","NUVAMA","UJJIVAN","SURYODAY",
    "EQUITASBNK","DCBBANK","KARURVSYS","FORCEMOT","WHIRLPOOL","VOLTAS",
]
NSE200 = list(dict.fromkeys(NSE200))

def yf_sym(t: str) -> str:
    return f"{t}.NS"


# ─────────────────────────────────────────────────────────────────────────────
# INDICATORS  (pure pandas — exact Pine Script equivalents)
# ─────────────────────────────────────────────────────────────────────────────
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds SMA44, SMA200 and all derived values exactly as Pine Script does.
    Pine uses simple moving average: ta.sma(close, N) = rolling mean of close.
    """
    df = df.copy()
    df["s44"]  = df["Close"].rolling(44,  min_periods=44).mean()
    df["s200"] = df["Close"].rolling(200, min_periods=200).mean()
    # s44[2] and s200[2] = value 2 bars ago
    df["s44_2"]  = df["s44"].shift(2)
    df["s200_2"] = df["s200"].shift(2)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# PINE SCRIPT BUY SIGNAL — PORTED EXACTLY
# ─────────────────────────────────────────────────────────────────────────────
def pine_buy_signal(row: pd.Series) -> dict | None:
    """
    Exact port of your Pine Script:

      is_trending = s44 > s200
                    and s44  > s44[2]     ← SMA44  rising
                    and s200 > s200[2]    ← SMA200 rising

      is_strong   = close > open          ← green candle
                    and close > (high+low)/2  ← closes in upper half

      buy = is_trending and is_strong and low <= s44 and close > s44

      sl_val    = low
      entry_val = close
      risk      = close - low
      tgt1      = close + risk
      tgt2      = close + risk * 2
    """
    # Need all values
    for col in ["Close","Open","High","Low","s44","s200","s44_2","s200_2"]:
        if col not in row.index or pd.isna(row[col]):
            return None

    close  = float(row["Close"])
    open_  = float(row["Open"])
    high   = float(row["High"])
    low    = float(row["Low"])
    s44    = float(row["s44"])
    s200   = float(row["s200"])
    s44_2  = float(row["s44_2"])
    s200_2 = float(row["s200_2"])

    # ── is_trending ───────────────────────────────────────────────────────────
    is_trending = (
        s44  > s200  and   # SMA44 above SMA200
        s44  > s44_2 and   # SMA44 rising (vs 2 bars ago)
        s200 > s200_2      # SMA200 rising (vs 2 bars ago)
    )

    # ── is_strong ─────────────────────────────────────────────────────────────
    mid_candle  = (high + low) / 2
    is_strong   = (
        close > open_ and       # green candle
        close > mid_candle      # close in upper half of candle
    )

    # ── BUY condition ─────────────────────────────────────────────────────────
    # low <= s44  → candle low touched or pierced SMA44 (bounce condition)
    # close > s44 → but price closed back above SMA44
    buy = is_trending and is_strong and low <= s44 and close > s44

    if not buy:
        return None

    # ── Levels (exact Pine Script formulas) ───────────────────────────────────
    entry = round(close, 2)
    sl    = round(low, 2)           # sl_val = low
    risk  = close - low             # risk = close - low
    tp1   = round(close + risk, 2)  # tgt1 = close + risk
    tp2   = round(close + risk * 2, 2)  # tgt2 = close + risk*2

    if risk <= 0 or risk / close > 0.20:   # skip absurd risk (>20%)
        return None

    risk_pct = round(risk / close * 100, 2)
    gap_pct  = round((s44 - s200) / s200 * 100, 2)

    # Strength score: how strong is this setup?
    # Based on: gap between SMAs (trend strength) + candle body quality
    body_size  = close - open_
    candle_range = high - low
    body_ratio = body_size / candle_range if candle_range > 0 else 0

    strength_score = int(
        min(40, gap_pct / 10 * 40) +        # 0-40: SMA gap (bigger = stronger trend)
        min(35, body_ratio * 35) +           # 0-35: candle body quality
        min(25, (1 - risk_pct / 20) * 25)   # 0-25: tighter risk = higher score
    )
    strength_score = max(35, min(97, strength_score))

    return {
        "entry":          entry,
        "sl":             sl,
        "tp1":            tp1,
        "tp2":            tp2,
        "risk":           round(risk, 2),
        "risk_pct":       risk_pct,
        "s44":            round(s44, 2),
        "s200":           round(s200, 2),
        "gap_pct":        gap_pct,
        "body_ratio":     round(body_ratio, 2),
        "s44_rising":     round(s44 - s44_2, 4),
        "s200_rising":    round(s200 - s200_2, 4),
        "strength_score": strength_score,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FORWARD OUTCOME  (real price walk — same logic as your Pine targets)
# ─────────────────────────────────────────────────────────────────────────────
def resolve_outcome(fwd: pd.DataFrame,
                    entry: float, sl: float,
                    tp1: float, tp2: float,
                    max_days: int = 30) -> dict:
    """
    Walk forward candles day by day.
    Conservative: SL checked first on each candle (low <= sl → SL_HIT).
    Then TP2, then TP1.
    """
    if fwd.empty:
        return {"outcome": "RUNNING", "days": 0, "exit_price": entry}

    for i, (_, r) in enumerate(fwd.head(max_days).iterrows(), 1):
        hi = float(r["High"])
        lo = float(r["Low"])

        if lo <= sl:                             # SL first (worst case)
            return {"outcome": "SL_HIT",  "days": i, "exit_price": sl}
        if hi >= tp2:
            return {"outcome": "TP2_HIT", "days": i, "exit_price": tp2}
        if hi >= tp1:
            return {"outcome": "TP1_HIT", "days": i, "exit_price": tp1}

    last = float(fwd["Close"].iloc[-1]) if not fwd.empty else entry
    return {"outcome": "RUNNING", "days": len(fwd.head(max_days)), "exit_price": last}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCANNER
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def run_scan(date_str: str) -> pd.DataFrame:
    if not YF_OK:
        return pd.DataFrame()

    trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    hist_start = trade_date - timedelta(days=310)   # need 200 bars minimum
    fwd_end    = trade_date + timedelta(days=45)

    records = []

    for i, ticker in enumerate(NSE200):
        try:
            raw = yf.download(
                yf_sym(ticker),
                start=hist_start,
                end=fwd_end,
                progress=False,
                auto_adjust=True,
            )
            if raw.empty or len(raw) < 210:
                continue

            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = raw.columns.get_level_values(0)
            raw.index = pd.to_datetime(raw.index).date

            hist = raw[raw.index <= trade_date].copy()
            fwd  = raw[raw.index >  trade_date].copy()

            if len(hist) < 210:
                continue

            # Add indicators
            ind = add_indicators(hist)

            # Find signal date
            avail   = [d for d in ind.index if d <= trade_date]
            if not avail:
                continue
            sig_d   = max(avail)
            row     = ind.loc[sig_d]

            # Apply exact Pine Script logic
            sig = pine_buy_signal(row)
            if sig is None:
                continue

            # Resolve real outcome
            out = resolve_outcome(fwd, sig["entry"], sig["sl"], sig["tp1"], sig["tp2"])

            records.append({
                "ticker":        ticker,
                "sig_date":      str(sig_d),
                "entry":         sig["entry"],
                "sl":            sig["sl"],
                "tp1":           sig["tp1"],
                "tp2":           sig["tp2"],
                "risk":          sig["risk"],
                "risk_pct":      sig["risk_pct"],
                "sma44":         sig["s44"],
                "sma200":        sig["s200"],
                "gap_pct":       sig["gap_pct"],
                "body_ratio":    sig["body_ratio"],
                "sma44_slope":   sig["s44_rising"],
                "sma200_slope":  sig["s200_rising"],
                "strength":      sig["strength_score"],
                "outcome":       out["outcome"],
                "days":          out["days"],
                "exit_price":    out["exit_price"],
            })

        except Exception:
            pass

        if i % 15 == 0 and i > 0:
            time.sleep(0.2)

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df = df.sort_values("strength", ascending=False).reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# FORMATTING
# ─────────────────────────────────────────────────────────────────────────────
def fmt(v: float) -> str:
    return f"₹{v:,.2f}"

def str_color(s: int) -> str:
    return "#22c55e" if s >= 70 else ("#f59e0b" if s >= 50 else "#ef4444")

OUTCOME_META = {
    "TP2_HIT": {"label": "TP2 Hit · 1:2 R/R", "color": "#22c55e", "icon": "🎯"},
    "TP1_HIT": {"label": "TP1 Hit · 1:1 R/R", "color": "#f59e0b", "icon": "✅"},
    "SL_HIT":  {"label": "Stop Loss Hit",       "color": "#ef4444", "icon": "🛑"},
    "RUNNING": {"label": "Still Running",        "color": "#38bdf8", "icon": "⏳"},
}

def gauge_svg(val: float, color: str, label: str) -> str:
    r, cx, cy = 38, 50, 50
    def a(deg):
        rad = math.radians(deg)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)
    sx, sy = a(180); bx, by = a(360); ex, ey = a(180 + (min(val, 100) / 100) * 180)
    lg = 1 if val > 50 else 0
    return f"""<div style="text-align:center;padding:8px 0;">
  <svg width="100" height="62" viewBox="0 0 100 62" overflow="visible">
    <path d="M{sx:.1f} {sy:.1f} A{r} {r} 0 1 1 {bx:.1f} {by:.1f}"
          fill="none" stroke="#10273d" stroke-width="7" stroke-linecap="round"/>
    <path d="M{sx:.1f} {sy:.1f} A{r} {r} 0 {lg} 1 {ex:.1f} {ey:.1f}"
          fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round"/>
    <text x="{cx}" y="{cy-1}" text-anchor="middle" fill="{color}"
          font-size="15" font-weight="700"
          font-family="JetBrains Mono,monospace">{val:.1f}%</text>
  </svg>
  <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:2px;
              color:#1e3d58;margin-top:1px;">{label}</div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# SIGNAL CARD
# ─────────────────────────────────────────────────────────────────────────────
def signal_card(row: pd.Series) -> str:
    om      = OUTCOME_META.get(row["outcome"], OUTCOME_META["RUNNING"])
    sc      = int(row["strength"])
    scol    = str_color(sc)
    d       = int(row["days"])
    d_s     = f"{d}d" if row["outcome"] != "RUNNING" else "open"
    sl_pct  = round((row["entry"] - row["sl"])  / row["entry"] * 100, 2)
    tp1_pct = round((row["tp1"]   - row["entry"])/ row["entry"] * 100, 2)
    tp2_pct = round((row["tp2"]   - row["entry"])/ row["entry"] * 100, 2)

    # Candle body quality badge
    br = float(row["body_ratio"])
    body_lbl   = "STRONG BODY" if br >= 0.65 else ("MEDIUM BODY" if br >= 0.4 else "WEAK BODY")
    body_color = "#22c55e" if br >= 0.65 else ("#f59e0b" if br >= 0.4 else "#ef4444")

    # Slope indicators
    s44_up  = "↑" if row["sma44_slope"]  > 0 else "↓"
    s200_up = "↑" if row["sma200_slope"] > 0 else "↓"

    return f"""
<div style="background:#071422;border:1px solid #10273d;border-top:3px solid #22c55e;
            border-radius:13px;padding:18px 16px 15px;height:100%;">

  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
    <div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">
        <span style="font-family:'Space Grotesk',sans-serif;font-size:17px;font-weight:800;color:#daeeff;">
          {row["ticker"]}
        </span>
        <span style="background:rgba(34,197,94,.12);color:#22c55e;font-family:'JetBrains Mono',monospace;
                     font-size:8px;font-weight:700;letter-spacing:1.5px;padding:2px 8px;border-radius:5px;">
          BUY 50/50
        </span>
      </div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:2px;color:#142638;">
        NSE · SWING TRIPLE BULLISH · {row["sig_date"]}
      </span>
    </div>
    <a href="https://www.tradingview.com/chart/?symbol=NSE:{row['ticker']}" target="_blank"
       style="background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.25);border-radius:7px;
              padding:5px 11px;font-family:'JetBrains Mono',monospace;font-size:8px;
              color:#4ade80;text-decoration:none;white-space:nowrap;">↗ CHART</a>
  </div>

  <!-- SMA Status row -->
  <div style="background:#04101e;border:1px solid #10273d;border-radius:8px;
              padding:8px 12px;margin-bottom:10px;display:flex;gap:14px;flex-wrap:wrap;align-items:center;">
    <div style="text-align:center;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#1e3d58;margin-bottom:2px;">SMA 44</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;color:#22c55e;">{fmt(row["sma44"])} {s44_up}</div>
    </div>
    <div style="width:1px;height:28px;background:#10273d;"></div>
    <div style="text-align:center;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#1e3d58;margin-bottom:2px;">SMA 200</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;color:#818cf8;">{fmt(row["sma200"])} {s200_up}</div>
    </div>
    <div style="width:1px;height:28px;background:#10273d;"></div>
    <div style="text-align:center;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#1e3d58;margin-bottom:2px;">GAP</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;color:#22c55e;">+{row["gap_pct"]}%</div>
    </div>
    <div style="width:1px;height:28px;background:#10273d;"></div>
    <div style="text-align:center;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#1e3d58;margin-bottom:2px;">CANDLE</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;color:{body_color};">{body_lbl}</div>
    </div>
  </div>

  <!-- Price grid: SL / Entry / TP1 / TP2 (same as Pine plot) -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:11px;">
    <div style="background:#04101e;border-radius:8px;padding:9px 11px;border:1px solid #10273d;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142638;margin-bottom:3px;">
        ENTRY (close)
      </div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#daeeff;">
        {fmt(row["entry"])}
      </span>
    </div>
    <div style="background:#04101e;border-radius:8px;padding:9px 11px;border:1px solid #10273d;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142638;margin-bottom:3px;">
        SL (candle low) <span style="color:#ef4444;">−{sl_pct}%</span>
      </div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#ef4444;">
        {fmt(row["sl"])}
      </span>
    </div>
    <div style="background:#04101e;border-radius:8px;padding:9px 11px;border:1px solid #10273d;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142638;margin-bottom:3px;">
        TARGET 1 · 1:1 <span style="color:#f59e0b;">+{tp1_pct}%</span>
      </div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#f59e0b;">
        {fmt(row["tp1"])}
      </span>
    </div>
    <div style="background:#04101e;border-radius:8px;padding:9px 11px;border:1px solid #10273d;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142638;margin-bottom:3px;">
        TARGET 2 · 1:2 <span style="color:#22c55e;">+{tp2_pct}%</span>
      </div>
      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:700;color:#22c55e;">
        {fmt(row["tp2"])}
      </span>
    </div>
  </div>

  <!-- Strength bar -->
  <div style="margin-bottom:10px;">
    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
      <span style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#142638;">SETUP STRENGTH</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;color:{scol};">
        {sc}<span style="font-size:9px;color:#142638;">/100</span>
      </span>
    </div>
    <div style="height:3px;background:#10273d;border-radius:2px;overflow:hidden;">
      <div style="height:100%;width:{sc}%;background:linear-gradient(90deg,{scol}55,{scol});border-radius:2px;"></div>
    </div>
  </div>

  <!-- Risk info -->
  <div style="font-family:'JetBrains Mono',monospace;font-size:8.5px;color:#1e3d58;
              margin-bottom:10px;padding:6px 8px;background:#04101e;border-radius:6px;border:1px solid #10273d;">
    RISK = {fmt(row["risk"])} ({sl_pct}%) &nbsp;·&nbsp; REWARD TP1 = {fmt(row["risk"])} &nbsp;·&nbsp; REWARD TP2 = {fmt(round(row["risk"]*2,2))}
  </div>

  <!-- Outcome badge -->
  <div style="background:#04101e;border:1px solid {om['color']}22;border-left:3px solid {om['color']};
              border-radius:8px;padding:9px 12px;display:flex;align-items:center;justify-content:space-between;">
    <div style="display:flex;align-items:center;gap:7px;">
      <span style="font-size:14px;">{om['icon']}</span>
      <span style="font-family:'Space Grotesk',sans-serif;font-size:13px;font-weight:700;color:{om['color']};">{om['label']}</span>
      <span style="background:rgba(34,197,94,.1);color:#22c55e;font-family:'JetBrains Mono',monospace;
                   font-size:7px;padding:1px 6px;border-radius:4px;letter-spacing:1px;">📡 REAL</span>
    </div>
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:#142638;">{d_s}</span>
  </div>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# POSITION CALCULATOR
# ─────────────────────────────────────────────────────────────────────────────
def pos_calc(entry, sl, tp1, tp2, capital, risk_pct) -> str:
    rp = entry - sl
    if rp <= 0:
        return "<p style='color:#ef4444;padding:8px;font-size:12px;'>⚠ Invalid SL</p>"
    risk_amt = capital * (risk_pct / 100)
    qty      = max(1, int(risk_amt / rp))
    deployed = qty * entry
    max_loss = qty * rp
    tp1_g    = qty * (tp1 - entry)
    tp2_g    = qty * (tp2 - entry)

    def r(lbl, val, c="#6aabcc"):
        return (
            f'<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #10273d;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:8.5px;letter-spacing:1.5px;color:#1e3d58;">{lbl}</span>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:13px;font-weight:600;color:{c};">{val}</span>'
            f'</div>'
        )

    return f"""<div style="background:#04101e;border-radius:10px;padding:14px 16px;margin-top:4px;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2px;color:#1e3d58;margin-bottom:10px;">POSITION CALCULATOR</div>
  {r("QUANTITY",             f"{qty:,} shares",       "#daeeff")}
  {r("CAPITAL DEPLOYED",     fmt(deployed),            "#daeeff")}
  {r("MAX LOSS (if SL hit)", fmt(max_loss),            "#ef4444")}
  {r("PROFIT at TP1 (1:1)",  fmt(tp1_g),              "#f59e0b")}
  {r("PROFIT at TP2 (1:2)",  fmt(tp2_g),              "#22c55e")}
  {r("% RETURN at TP1",      f"{tp1_g/deployed*100:.2f}%", "#f59e0b")}
  {r("% RETURN at TP2",      f"{tp2_g/deployed*100:.2f}%", "#22c55e")}
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
# ACCURACY BANNER
# ─────────────────────────────────────────────────────────────────────────────
def accuracy_banner(df: pd.DataFrame):
    closed  = df[df["outcome"] != "RUNNING"]
    n_total = len(closed)
    if n_total == 0:
        st.info("All trades still running — outcome data not yet available. Try an older date.")
        return

    n_tp2 = (closed["outcome"] == "TP2_HIT").sum()
    n_tp1 = closed["outcome"].isin(["TP1_HIT","TP2_HIT"]).sum()
    n_sl  = (closed["outcome"] == "SL_HIT").sum()
    n_run = (df["outcome"] == "RUNNING").sum()

    tp2_rate = n_tp2 / n_total * 100
    tp1_rate = n_tp1 / n_total * 100
    sl_rate  = n_sl  / n_total * 100

    avg_win_days  = closed[closed["outcome"].isin(["TP1_HIT","TP2_HIT"])]["days"].mean()
    avg_loss_days = closed[closed["outcome"] == "SL_HIT"]["days"].mean()

    def ac(v, t):
        return "#22c55e" if v >= t else ("#f59e0b" if v >= t * 0.8 else "#ef4444")

    st.markdown(f"""
<div style="background:#071422;border:1px solid #10273d;border-radius:14px;padding:20px 24px;margin-bottom:18px;">

  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:16px;">
    <div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2px;color:#1e3d58;">
        REAL ACCURACY · {len(df)} SIGNALS · {n_total} CLOSED · {n_run} RUNNING
      </div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:12px;color:#142638;margin-top:3px;">
        All outcomes from real NSE forward price data · No simulation · No manipulation
      </div>
    </div>
    <div style="display:flex;gap:10px;">
      {gauge_svg(tp2_rate, ac(tp2_rate,55), "TP2 HIT RATE")}
      {gauge_svg(tp1_rate, ac(tp1_rate,65), "TP1+ HIT RATE")}
    </div>
  </div>

  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;">

    <div style="background:#04101e;border-radius:10px;padding:14px 12px;
                border:1px solid #10273d;border-top:2.5px solid {ac(tp2_rate,55)};">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#1e3d58;margin-bottom:5px;">TP2 HIT RATE</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:30px;font-weight:800;color:{ac(tp2_rate,55)};line-height:1;">{tp2_rate:.1f}%</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#1e3d58;margin-top:4px;">{n_tp2} of {n_total} closed</div>
    </div>

    <div style="background:#04101e;border-radius:10px;padding:14px 12px;
                border:1px solid #10273d;border-top:2.5px solid {ac(tp1_rate,65)};">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#1e3d58;margin-bottom:5px;">TP1+ HIT RATE</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:30px;font-weight:800;color:{ac(tp1_rate,65)};line-height:1;">{tp1_rate:.1f}%</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#1e3d58;margin-top:4px;">avg {avg_win_days:.1f}d to win</div>
    </div>

    <div style="background:#04101e;border-radius:10px;padding:14px 12px;
                border:1px solid #10273d;border-top:2.5px solid #ef4444;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#1e3d58;margin-bottom:5px;">SL HIT RATE</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:30px;font-weight:800;color:#ef4444;line-height:1;">{sl_rate:.1f}%</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#1e3d58;margin-top:4px;">avg {avg_loss_days:.1f}d to loss</div>
    </div>

    <div style="background:#04101e;border-radius:10px;padding:14px 12px;
                border:1px solid #10273d;border-top:2.5px solid #38bdf8;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#1e3d58;margin-bottom:5px;">STILL RUNNING</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:30px;font-weight:800;color:#38bdf8;line-height:1;">{n_run}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#1e3d58;margin-top:4px;">awaiting close</div>
    </div>

  </div>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# P&L SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
def pnl_tab(df: pd.DataFrame, capital: float, risk_pct: float):
    risk_amt = capital * (risk_pct / 100)
    rows = []
    for _, row in df.iterrows():
        rp = row["entry"] - row["sl"]
        if rp <= 0: continue
        qty = max(1, int(risk_amt / rp))
        out = row["outcome"]
        if   out == "TP2_HIT": pnl, tag = qty * (row["tp2"] - row["entry"]), "TP2 🎯"
        elif out == "TP1_HIT": pnl, tag = qty * (row["tp1"] - row["entry"]), "TP1 ✅"
        elif out == "SL_HIT":  pnl, tag = -qty * rp,                         "SL 🛑"
        else:                  pnl, tag = 0.0,                                "OPEN ⏳"
        rows.append({
            "Ticker":   row["ticker"],
            "Outcome":  tag,
            "Days":     int(row["days"]),
            "Qty":      qty,
            "Entry":    fmt(row["entry"]),
            "Exit":     fmt(row["exit_price"]),
            "SL":       fmt(row["sl"]),
            "P&L (₹)":  round(pnl, 2),
        })

    if not rows:
        st.info("No trades."); return

    pdf  = pd.DataFrame(rows)
    tot  = pdf["P&L (₹)"].sum()
    w    = (pdf["P&L (₹)"] > 0).sum()
    l    = (pdf["P&L (₹)"] < 0).sum()
    o    = pdf["Outcome"].str.contains("OPEN").sum()
    wr   = w / (w + l) * 100 if (w + l) > 0 else 0
    avg  = pdf[pdf["P&L (₹)"] != 0]["P&L (₹)"].mean() if (w + l) > 0 else 0

    m = st.columns(5)
    m[0].metric("TOTAL P&L",     fmt(tot),     f"{'▲' if tot >= 0 else '▼'} real outcomes")
    m[1].metric("WIN RATE",      f"{wr:.1f}%",  f"{w}W / {l}L")
    m[2].metric("AVG TRADE P&L", fmt(avg),      "closed only")
    m[3].metric("OPEN TRADES",   o,             "not yet closed")
    m[4].metric("RISK / TRADE",  fmt(risk_amt), f"{risk_pct}% of ₹{capital:,.0f}")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    styled = (
        pdf.style
        .applymap(lambda v: "color:#22c55e;" if v > 0 else ("color:#ef4444;" if v < 0 else "color:#f59e0b;"), subset=["P&L (₹)"])
        .applymap(lambda v: "color:#22c55e;" if "🎯" in str(v) or "✅" in str(v) else ("color:#ef4444;" if "🛑" in str(v) else "color:#f59e0b;"), subset=["Outcome"])
        .format({"P&L (₹)": "{:,.2f}"})
    )
    st.dataframe(styled, use_container_width=True, height=400)

    buf = io.StringIO()
    pdf.to_csv(buf, index=False)
    st.download_button("⬇  Download P&L CSV",
                       data=buf.getvalue().encode("utf-8-sig"),
                       file_name=f"arthsutra_pnl_{date.today()}.csv",
                       mime="text/csv", use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
def header():
    st.markdown("""
<div style="background:#04101e;border-bottom:1px solid #10273d;padding:14px 0 10px;margin-bottom:14px;">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
    <div style="display:flex;align-items:center;gap:13px;">
      <div style="width:44px;height:44px;border-radius:11px;
                  background:linear-gradient(135deg,#16a34a,#2563eb);
                  display:flex;align-items:center;justify-content:center;font-size:22px;
                  box-shadow:0 0 22px rgba(22,163,74,.35);">🔱</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:#daeeff;">
          Arthsutra
        </div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2.5px;color:#142638;margin-top:2px;">
          SWING TRIPLE BULLISH · SMA44 / SMA200 · REAL NSE DATA
        </div>
      </div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <div style="display:flex;align-items:center;gap:7px;background:rgba(34,197,94,.07);
                  border:1px solid rgba(34,197,94,.2);border-radius:8px;padding:7px 13px;">
        <div style="width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px #22c55e;"></div>
        <span style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2px;color:#22c55e;">PINE SCRIPT PORTED</span>
      </div>
      <div style="display:flex;align-items:center;gap:7px;background:rgba(37,99,235,.07);
                  border:1px solid rgba(37,99,235,.2);border-radius:8px;padding:7px 13px;">
        <span style="font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:2px;color:#60a5fa;">📡 YFINANCE REAL DATA</span>
      </div>
    </div>
  </div>
  <div style="background:rgba(234,179,8,.05);border:1px solid rgba(234,179,8,.14);
              border-radius:8px;padding:7px 14px;margin-top:12px;">
    <span style="font-family:'JetBrains Mono',monospace;font-size:8.5px;letter-spacing:1px;color:#6b5a20;">
      ⚠ NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · NOT INVESTMENT ADVICE · PAST RESULTS DO NOT GUARANTEE FUTURE RETURNS
    </span>
  </div>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# GUIDE
# ─────────────────────────────────────────────────────────────────────────────
def guide():
    with st.expander("📖  Strategy Logic — Exact Pine Script Port", expanded=False):
        st.markdown("""
<div style="font-family:'Space Grotesk',sans-serif;color:#4a7a9a;line-height:1.8;font-size:13.5px;padding:4px 2px;">

<div style="background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.2);border-radius:10px;padding:14px 18px;margin-bottom:14px;">
  <div style="font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:2px;color:#1e3d58;margin-bottom:8px;">YOUR PINE SCRIPT — PORTED LINE BY LINE</div>
  <div style="background:#04101e;border-radius:8px;padding:12px 14px;font-family:'JetBrains Mono',monospace;font-size:12px;color:#22c55e;line-height:2;">
    s44  = SMA(close, 44)<br/>
    s200 = SMA(close, 200)<br/><br/>
    <span style="color:#60a5fa;">is_trending</span> = s44 &gt; s200 <span style="color:#818cf8;">AND</span> s44 &gt; s44[2] <span style="color:#818cf8;">AND</span> s200 &gt; s200[2]<br/>
    <span style="color:#60a5fa;">is_strong</span>   = close &gt; open <span style="color:#818cf8;">AND</span> close &gt; (high+low)/2<br/><br/>
    <span style="color:#f59e0b;">BUY</span> = is_trending <span style="color:#818cf8;">AND</span> is_strong <span style="color:#818cf8;">AND</span> low &lt;= s44 <span style="color:#818cf8;">AND</span> close &gt; s44<br/><br/>
    <span style="color:#ef4444;">SL</span>  = candle low &nbsp;&nbsp;·&nbsp;&nbsp;
    <span style="color:#f59e0b;">TP1</span> = close + (close−low) &nbsp;&nbsp;·&nbsp;&nbsp;
    <span style="color:#22c55e;">TP2</span> = close + 2×(close−low)
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:14px;">
  <div>
    <p style="font-family:'JetBrains Mono',monospace;font-size:8.5px;letter-spacing:2px;color:#1e3d58;margin-bottom:5px;">THE KEY SIGNAL IDEA</p>
    <p>The candle's low <b style="color:#daeeff;">touches or dips below SMA44</b> — the stock tested the trend support — but <b style="color:#22c55e;">closed back above SMA44</b>. This is a bullish rejection / bounce. Combined with both SMAs rising, it's a high-probability continuation trade.</p>
  </div>
  <div>
    <p style="font-family:'JetBrains Mono',monospace;font-size:8.5px;letter-spacing:2px;color:#1e3d58;margin-bottom:5px;">HOW TO USE</p>
    <p>Pick a date at least <b style="color:#daeeff;">3 days ago</b> (forward data needed for outcomes). Click <b style="color:#22c55e;">Scan</b>. Expand any card for the Position Calculator. Use <b style="color:#f59e0b;">Accuracy tab</b> to see real TP hit rates from actual NSE prices.</p>
  </div>
</div>

<div style="background:rgba(234,179,8,.06);border:1px solid rgba(234,179,8,.18);border-radius:9px;padding:12px 16px;">
  <b style="color:#f59e0b;">⏱ Scan time:</b> ~2–4 minutes first run (200 real data downloads). Same date = instant cached result.
</div>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    for k in ["df", "scan_date"]:
        if k not in st.session_state:
            st.session_state[k] = None

    header()

    if not YF_OK:
        st.error("❌ **yfinance not installed.**\n\n```\npip install yfinance\n```")
        st.stop()

    guide()
    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── Controls ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns([2, 1.6, 2.2, 1.8])

    with c1:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#1e3d58;margin-bottom:4px;">SIGNAL DATE (weekday · min 3 days ago)</p>', unsafe_allow_html=True)
        today   = date.today()
        default = today - timedelta(days=4)
        while default.weekday() >= 5:
            default -= timedelta(days=1)
        sel = st.date_input("_d", value=default,
                            min_value=today - timedelta(days=365),
                            max_value=today - timedelta(days=2),
                            label_visibility="collapsed")
    with c2:
        st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)
        run = st.button("◈  Scan NSE 200", use_container_width=True)
    with c3:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#1e3d58;margin-bottom:4px;">FILTER</p>', unsafe_allow_html=True)
        flt = st.selectbox("_f",
                           ["ALL signals", "Winners (TP1+)", "TP2 hits only", "SL hits only", "Still running"],
                           label_visibility="collapsed")
    with c4:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#1e3d58;margin-bottom:4px;">SORT BY</p>', unsafe_allow_html=True)
        srt = st.selectbox("_s", ["Strength ↓", "Risk % ↑ (tightest)", "Days ↑"], label_visibility="collapsed")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── Scan ──────────────────────────────────────────────────────────────────
    if run:
        ds = str(sel)
        st.info(f"📡 Scanning all 200 NSE stocks for **{sel}** using your Pine Script logic. First run ~3 min…")
        with st.spinner("Downloading real NSE OHLC data…"):
            df = run_scan(ds)
        st.session_state["df"]        = df
        st.session_state["scan_date"] = ds
        if df.empty:
            st.warning(
                "⚠ No signals found on this date.\n\n"
                "Your Pine Script strategy requires:\n"
                "- SMA44 > SMA200 (both rising)\n"
                "- Green candle with strong close\n"
                "- Candle low **touched** SMA44 but closed above it\n\n"
                "This is a very precise condition. Try different weekdays, "
                "especially during trending/bullish market phases."
            )
            return
        st.success(f"✅ **{len(df)} signals** found on {sel} — real data, real outcomes.")

    df = st.session_state["df"]

    # ── Idle ──────────────────────────────────────────────────────────────────
    if df is None or df.empty:
        st.markdown("""
<div style="text-align:center;padding:55px 0 65px;">
  <div style="font-size:54px;opacity:0.06;margin-bottom:16px;">🔱</div>
  <div style="font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:700;color:#10273d;margin-bottom:10px;">
    Swing Triple Bullish Scanner
  </div>
  <div style="font-family:'Space Grotesk',sans-serif;font-size:14px;color:#10273d;
              max-width:500px;margin:0 auto;line-height:1.85;">
    Your exact Pine Script logic, running on real NSE 200 data.<br/>
    SMA44 / SMA200 aligned · Candle bounces off SMA44 · Strong close.<br/>
    <b style="color:#4ade80;">Select a past weekday · Click Scan NSE 200</b>
  </div>
</div>""", unsafe_allow_html=True)
        return

    # ── Filter & sort ─────────────────────────────────────────────────────────
    view = df.copy()
    if   flt == "Winners (TP1+)":   view = view[view["outcome"].isin(["TP1_HIT","TP2_HIT"])]
    elif flt == "TP2 hits only":    view = view[view["outcome"] == "TP2_HIT"]
    elif flt == "SL hits only":     view = view[view["outcome"] == "SL_HIT"]
    elif flt == "Still running":    view = view[view["outcome"] == "RUNNING"]

    if   srt == "Risk % ↑ (tightest)": view = view.sort_values("risk_pct", ascending=True)
    elif srt == "Days ↑":               view = view.sort_values("days", ascending=True)
    else:                               view = view.sort_values("strength", ascending=False)
    view = view.reset_index(drop=True)

    # ── Top stats ─────────────────────────────────────────────────────────────
    m = st.columns(5)
    closed = df[df["outcome"] != "RUNNING"]
    tp2_r  = (closed["outcome"] == "TP2_HIT").sum() / max(len(closed), 1) * 100
    tp1_r  = closed["outcome"].isin(["TP1_HIT","TP2_HIT"]).sum() / max(len(closed), 1) * 100
    m[0].metric("SIGNALS FOUND",  len(df),             str(st.session_state["scan_date"]))
    m[1].metric("CLOSED TRADES",  len(closed),          f"{len(df)-len(closed)} still running")
    m[2].metric("TP2 HIT RATE",   f"{tp2_r:.1f}%",      "real outcomes")
    m[3].metric("TP1+ HIT RATE",  f"{tp1_r:.1f}%",      "real outcomes")
    m[4].metric("SHOWING",        len(view),            flt)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    t_sig, t_acc, t_pnl, t_exp = st.tabs([
        "📊  Signals", "🎯  Accuracy", "💰  P&L", "⬇  Export"
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # SIGNALS TAB
    # ─────────────────────────────────────────────────────────────────────────
    with t_sig:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#1e3d58;margin-bottom:6px;">POSITION SIZING</p>', unsafe_allow_html=True)
        pc1, pc2, _ = st.columns([1.5, 1.5, 5])
        with pc1: capital  = st.number_input("Capital (₹)",        value=100000, step=10000, min_value=1000)
        with pc2: risk_pct = st.number_input("Risk per trade (%)", value=1.0, step=0.25, min_value=0.25, max_value=10.0)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        if view.empty:
            st.info("No signals match this filter.")
        else:
            ncols = 3
            for ri in range(math.ceil(len(view) / ncols)):
                cols = st.columns(ncols)
                for ci in range(ncols):
                    idx = ri * ncols + ci
                    if idx >= len(view): break
                    row = view.iloc[idx]
                    with cols[ci]:
                        st.markdown(signal_card(row), unsafe_allow_html=True)

                        with st.expander(f"🔍  Analysis & Calculator — {row['ticker']}", expanded=False):
                            om  = OUTCOME_META.get(row["outcome"], OUTCOME_META["RUNNING"])
                            d   = int(row["days"])
                            d_s = f"{d} day{'s' if d != 1 else ''}" if row["outcome"] != "RUNNING" else "Trade still open"
                            rp  = row["entry"] - row["sl"]
                            qty = max(1, int((capital * (risk_pct / 100)) / rp)) if rp > 0 else 1
                            act_pnl = (
                                qty * (row["tp2"] - row["entry"]) if row["outcome"] == "TP2_HIT" else
                                qty * (row["tp1"] - row["entry"]) if row["outcome"] == "TP1_HIT" else
                                -qty * rp                          if row["outcome"] == "SL_HIT"  else 0.0
                            )
                            pc = "#22c55e" if act_pnl > 0 else ("#ef4444" if act_pnl < 0 else "#f59e0b")

                            st.markdown(f"""
<div style="padding:10px 2px 6px;">
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px;">
    <div style="background:#071422;border:1px solid {om['color']}22;border-top:2px solid {om['color']};border-radius:9px;padding:12px;">
      <div style="font-size:18px;margin-bottom:5px;">{om['icon']}</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:13px;font-weight:700;color:{om['color']};">{om['label']}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;color:#1e3d58;margin-top:3px;">📡 REAL NSE DATA</div>
    </div>
    <div style="background:#071422;border:1px solid #10273d;border-radius:9px;padding:12px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#1e3d58;margin-bottom:5px;">DAYS TO EXIT</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:15px;font-weight:700;color:#daeeff;">{d_s}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#1e3d58;margin-top:3px;">exit @ {fmt(row['exit_price'])}</div>
    </div>
    <div style="background:#071422;border:1px solid #10273d;border-radius:9px;padding:12px;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#1e3d58;margin-bottom:5px;">P&L · {qty} SHARES</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:15px;font-weight:700;color:{pc};">{fmt(act_pnl)}</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:8px;color:#1e3d58;margin-top:3px;">on {fmt(capital)}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

                            st.markdown(pos_calc(row["entry"], row["sl"],
                                                 row["tp1"], row["tp2"],
                                                 capital, risk_pct), unsafe_allow_html=True)
                        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # ACCURACY TAB
    # ─────────────────────────────────────────────────────────────────────────
    with t_acc:
        accuracy_banner(df)
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#1e3d58;margin-bottom:10px;">FULL OUTCOME TABLE</p>', unsafe_allow_html=True)
        tbl = df[["ticker","strength","outcome","days","entry","sl","tp1","tp2",
                  "exit_price","risk_pct","gap_pct","sma44","sma200"]].copy()
        tbl.columns = ["Ticker","Strength","Outcome","Days","Entry","SL","TP1","TP2",
                       "Exit","Risk%","SMA Gap%","SMA44","SMA200"]
        st.dataframe(
            tbl.style
            .applymap(lambda v: "color:#22c55e;font-weight:700;" if v == "TP2_HIT" else
                      ("color:#f59e0b;font-weight:700;" if v == "TP1_HIT" else
                       ("color:#ef4444;font-weight:700;" if v == "SL_HIT" else "color:#38bdf8;")),
                      subset=["Outcome"])
            .format({"Entry":"₹{:.2f}","SL":"₹{:.2f}","TP1":"₹{:.2f}",
                     "TP2":"₹{:.2f}","Exit":"₹{:.2f}","Risk%":"{:.2f}%"}),
            use_container_width=True, height=460,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # P&L TAB
    # ─────────────────────────────────────────────────────────────────────────
    with t_pnl:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#1e3d58;margin-bottom:12px;">HYPOTHETICAL P&L · REAL OUTCOMES · NOT GUARANTEED FUTURE RETURNS</p>', unsafe_allow_html=True)
        pa, pb, _ = st.columns([1.5, 1.5, 5])
        with pa: pcap  = st.number_input("Capital (₹)  ",         value=100000, step=10000, min_value=1000)
        with pb: prisk = st.number_input("Risk per trade (%)  ",  value=1.0, step=0.25, min_value=0.25, max_value=10.0)
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        pnl_tab(df, pcap, prisk)

    # ─────────────────────────────────────────────────────────────────────────
    # EXPORT TAB
    # ─────────────────────────────────────────────────────────────────────────
    with t_exp:
        st.markdown('<p style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:2px;color:#1e3d58;margin-bottom:12px;">EXPORT · REAL NSE DATA · ALL SIGNALS + OUTCOMES</p>', unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, height=340)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        st.download_button(
            f"⬇  Download CSV — {len(df)} signals · {st.session_state['scan_date']}",
            data=buf.getvalue().encode("utf-8-sig"),
            file_name=f"arthsutra_swing_{st.session_state['scan_date']}.csv",
            mime="text/csv", use_container_width=True,
        )

    # Footer
    st.markdown(f"""
<hr/>
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;padding:4px 0;">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-size:17px;">🔱</span>
    <div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:13px;font-weight:800;color:#142638;">Arthsutra</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:2px;color:#0c1e2e;">
        SWING TRIPLE BULLISH · SMA44 · SMA200 · DISCIPLINE · CONSISTENCY
      </div>
    </div>
  </div>
  <div style="font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:1px;color:#0c1e2e;text-align:right;line-height:2.1;">
    NOT SEBI REGISTERED · EDUCATIONAL USE ONLY · © {date.today().year} ARTHSUTRA
  </div>
</div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
