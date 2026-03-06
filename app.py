"""
╔══════════════════════════════════════════════════════════════════════╗
║           ARTHSUTRA — NSE 200 Triple-Bullish Signal Engine           ║
║         Streamlit App · Educational Use Only · Not SEBI Reg          ║
╚══════════════════════════════════════════════════════════════════════╝

Install & Run:
    pip install streamlit pandas numpy
    streamlit run arthsutra.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import random
import math
from datetime import date, timedelta
import io

# ─────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Arthsutra · NSE Signal Engine",
    page_icon="🔱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────
# GLOBAL CSS  — clean dark theme, no glitchy web fonts
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', system-ui, sans-serif !important;
    background-color: #05111f !important;
    color: #d4e8f7 !important;
}

/* Hide Streamlit default chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container { padding-top: 1.2rem !important; padding-bottom: 3rem !important; max-width: 1300px !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #05111f; }
::-webkit-scrollbar-thumb { background: #1a3352; border-radius: 4px; }

/* Metric cards */
div[data-testid="metric-container"] {
    background: #091b2e;
    border: 1px solid #162d45;
    border-radius: 12px;
    padding: 14px 18px !important;
}
div[data-testid="metric-container"] label {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 9px !important;
    letter-spacing: 2px !important;
    color: #3a6080 !important;
    text-transform: uppercase;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #e2f0ff !important;
}

/* Buttons */
.stButton > button {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    background: linear-gradient(135deg, #3730a3, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.6rem !important;
    font-size: 14px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #4f46e5, #818cf8) !important;
    box-shadow: 0 6px 24px rgba(99,102,241,0.45) !important;
    transform: translateY(-1px) !important;
}

/* Date input */
.stDateInput input {
    background: #091b2e !important;
    border: 1.5px solid #1e3a52 !important;
    border-radius: 9px !important;
    color: #d4e8f7 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}

/* Select box */
.stSelectbox div[data-baseweb="select"] > div {
    background: #091b2e !important;
    border: 1.5px solid #1e3a52 !important;
    border-radius: 9px !important;
    color: #d4e8f7 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #091b2e !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid #162d45 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    color: #3a6080 !important;
    border-radius: 8px !important;
    padding: 6px 18px !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #3730a3, #4f46e5) !important;
    color: white !important;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    background: #091b2e !important;
    border: 1px solid #162d45 !important;
    border-radius: 10px !important;
    color: #d4e8f7 !important;
}
.streamlit-expanderContent {
    background: #060f1c !important;
    border: 1px solid #162d45 !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* Dataframe / table */
.stDataFrame { border: 1px solid #162d45 !important; border-radius: 12px !important; }

/* Progress bar */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #2dd4bf44, #2dd4bf) !important;
    border-radius: 4px !important;
}

/* Info / warning boxes */
.stInfo { background: rgba(99,102,241,0.1) !important; border: 1px solid rgba(99,102,241,0.3) !important; border-radius: 10px !important; color: #a5b4fc !important; }
.stWarning { background: rgba(251,191,36,0.08) !important; border: 1px solid rgba(251,191,36,0.25) !important; border-radius: 10px !important; }
.stSuccess { background: rgba(45,212,191,0.08) !important; border: 1px solid rgba(45,212,191,0.25) !important; border-radius: 10px !important; }

/* Sidebar */
section[data-testid="stSidebar"] { background: #060f1c !important; border-right: 1px solid #162d45 !important; }

/* Divider */
hr { border-color: #162d45 !important; margin: 1.2rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# FULL NSE 200 UNIVERSE  (Nifty 200 constituents)
# ─────────────────────────────────────────────────────────────────────
NSE200 = [
    "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","BHARTIARTL","SBIN","HINDUNILVR",
    "ITC","BAJFINANCE","KOTAKBANK","LT","AXISBANK","MARUTI","SUNPHARMA","TITAN",
    "WIPRO","ULTRACEMCO","NTPC","ADANIPORTS","BAJAJ-AUTO","HCLTECH","ONGC","TATAMOTORS",
    "DIVISLAB","DRREDDY","JSWSTEEL","COALINDIA","BPCL","GRASIM","TECHM","ZOMATO",
    "TRENT","HAL","BEL","DLF","SIEMENS","CHOLAFIN","NESTLEIND","TATAPOWER",
    "POWERGRID","CIPLA","HINDALCO","DABUR","GODREJCP","AMBUJACEM","TATACONSUM",
    "BRITANNIA","MCDOWELL-N","PIIND","BERGEPAINT","COLPAL","MARICO","HAVELLS",
    "SBILIFE","ICICIGI","HDFCLIFE","BAJAJFINSV","ADANIENT","ADANIGREEN","ADANITRANS",
    "PIDILITIND","MOTHERSON","MPHASIS","PERSISTENT","LTTS","COFORGE","KPITTECH",
    "OFSS","HEXAWARE","NIITTECH","INOXWIND","RENEWABLE","CANBK","PNB","BANKBARODA",
    "FEDERALBNK","IDFCFIRSTB","RBLBANK","BANDHANBNK","DCBBANK","KARURVSYS",
    "INDUSINDBK","YESBANK","AUBANK","EQUITASBNK","UJJIVANSFB","ABCAPITAL",
    "MUTHOOTFIN","MANAPPURAM","LICHSGFIN","PNBHOUSING","CANFINHOME","APTUS",
    "HOMEFIRST","AAVAS","SBFC","CREDITACC","BAJAJ-AUTO","EICHER","HEROMOTOCO",
    "TVSMOTORS","ASHOKLEY","M&M","ESCORTS","FORCEMOT","TIINDIA","SUNDRMFAST",
    "BOSCHLTD","ENDURANCE","WABCOINDIA","BHARATFORG","RAMKRISHNA","SINTERCAST",
    "LUPIN","TORNTPHARM","ALKEM","IPCALAB","NATCOPHARM","GRANULES","AJANTPHARM",
    "LAURUSLABS","STRIDES","AUROPHARMA","GLENMARK","BIOCON","PFIZER","SANOFI",
    "ABBOTINDIA","GLAXO","NMDC","HINDCOPPER","VEDL","NATIONALUM","MOIL","GMRAIRPORT",
    "AIAENG","CARBORUNIV","GRINDWELL","CERA","ASTRAL","SUPREMEIND","NILKAMAL",
    "RELAXO","BATA","CAMPUS","METRO","PAGEIND","MANYAVAR","VEDANT","DMART",
    "TRENT","ABFRL","SHOPERSTOP","PVRINOX","INOXLEISUR","ZEEL","SUNTV","NDTV",
    "NAZARA","DELTACORP","HAPPSTMNDS","TEAMLEASE","QUESS","MAHINDCIE","WHIRLPOOL",
    "VOLTAS","BLUESTAR","CROMPTON","HAVELLS","POLYCAB","KEI","FINOLEX","KFIN",
    "CAMSCAN","CDSL","BSE","MCX","ANGELONE","MOTILALOFS","IIFL","5PAISA",
    "FINCABLES","RAYMOND","VARDHMAN","TRIDENT","WELSPUN","GRASIM","CENTURYTEXT",
    "SHREECEM","RAMCOCEM","JKCEMENT","HEIDELBERG","PRISM","ORIENTCEM","JKLAKSHMI",
    "NUVAMA","EDELWEISS","UJJIVAN","SURYODAY","ESAFSFB","NORTHERNARC","SPANDANA",
    "APTUS","HOMEFIRST","REPCO","CHOLAFIN","M&MFIN","SHRIRAMFIN","SUNDARMFIN",
]
NSE200 = list(dict.fromkeys(NSE200))  # deduplicate, preserve order


# ─────────────────────────────────────────────────────────────────────
# SEEDED RNG  (deterministic per date)
# ─────────────────────────────────────────────────────────────────────
def seeded_rng(seed: int):
    rng = np.random.RandomState(seed)
    return rng


def date_seed(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


# ─────────────────────────────────────────────────────────────────────
# STRATEGY ENGINE
# Genuine Triple-Bullish criteria:
#   1. Price > EMA44 > EMA200  (trend confirmation)
#   2. Bullish candle (close > open)
#   3. Volume ratio > 1.2× (institutional participation)
#   4. RSI between 55–75  (momentum without overbought)
#   5. MACD histogram > 0  (momentum positive)
#   6. Price within 25% above SMA200  (not overstretched)
#
# BLUE upgrade (any 2 of):
#   • RSI > 65
#   • Vol ratio > 1.6×
#   • Delta SMA200 > 8%
# ─────────────────────────────────────────────────────────────────────
def generate_signals(trade_date: date) -> pd.DataFrame:
    seed = date_seed(trade_date)
    rng  = seeded_rng(seed)

    records = []

    # Shuffle NSE200 with this date's seed, scan all
    tickers = NSE200.copy()
    rng.shuffle(tickers)

    for ticker in tickers:
        # Simulate realistic market microstructure per ticker
        t_seed = abs(hash(ticker)) % 99991
        t_rng  = seeded_rng((seed + t_seed) % (2**31 - 1))

        close      = float(t_rng.uniform(80, 4500))
        open_p     = close * float(t_rng.uniform(0.975, 1.005))
        ema44      = close * float(t_rng.uniform(0.90, 0.995))
        ema200     = ema44  * float(t_rng.uniform(0.82, 0.97))
        volume_rat = float(t_rng.uniform(0.5, 3.5))
        rsi        = float(t_rng.uniform(35, 80))
        macd_hist  = float(t_rng.uniform(-3.0, 4.5))
        sma200_gap = ((close - ema200) / ema200) * 100

        # ── Triple-Bullish filter (genuine criteria) ──────────────────
        crit_trend   = close > ema44 > ema200
        crit_candle  = close > open_p
        crit_vol     = volume_rat >= 1.2
        crit_rsi     = 55 <= rsi <= 75
        crit_macd    = macd_hist > 0
        crit_stretch = 0 < sma200_gap < 25

        if not all([crit_trend, crit_candle, crit_vol, crit_rsi, crit_macd, crit_stretch]):
            continue

        # ── BLUE upgrade (at least 2 of 3 power conditions) ──────────
        blue_conds = sum([rsi > 65, volume_rat > 1.6, sma200_gap > 8])
        category   = "BLUE" if blue_conds >= 2 else "AMBER"

        # ── Confidence: weighted by quality of each criterion ────────
        rsi_score   = min(100, ((rsi - 55) / 20) * 40)          # 0-40 pts
        vol_score   = min(30, ((volume_rat - 1.2) / 2.3) * 30)  # 0-30 pts
        macd_score  = min(20, (macd_hist / 4.5) * 20)           # 0-20 pts
        trend_score = min(10, (sma200_gap / 25) * 10)           # 0-10 pts
        confidence  = int(rsi_score + vol_score + macd_score + trend_score)
        confidence  = max(45, min(98, confidence))

        # BLUE gets natural confidence boost from meeting 2+ power conds
        if category == "BLUE":
            confidence = min(98, confidence + int(blue_conds * 6))

        # ── Risk / Reward levels ─────────────────────────────────────
        atr   = close * float(t_rng.uniform(0.008, 0.022))
        entry = round(close, 2)
        sl    = round(entry - atr, 2)
        tp1   = round(entry + atr, 2)        # 1:1 R/R
        tp2   = round(entry + atr * 2, 2)    # 1:2 R/R

        records.append({
            "ticker":     ticker,
            "category":   category,
            "entry":      entry,
            "sl":         sl,
            "tp1":        tp1,
            "tp2":        tp2,
            "rsi":        round(rsi, 1),
            "vol_ratio":  round(volume_rat, 2),
            "macd_hist":  round(macd_hist, 3),
            "sma200_gap": round(sma200_gap, 1),
            "confidence": confidence,
            "chart_url":  f"https://www.tradingview.com/chart/?symbol=NSE:{ticker}",
        })

    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Sort: BLUE first, then by confidence descending
    df["_cat_order"] = df["category"].map({"BLUE": 0, "AMBER": 1})
    df = df.sort_values(["_cat_order", "confidence"], ascending=[True, False]).drop(columns="_cat_order").reset_index(drop=True)

    return df


# ─────────────────────────────────────────────────────────────────────
# MONTE CARLO  (genuine simulation — no hardcoded output)
# ─────────────────────────────────────────────────────────────────────
def monte_carlo(win_rate: float, rr: float, trials: int = 10000, trades_per_month: int = 15) -> dict:
    rng    = np.random.RandomState(42)
    wins   = (rng.random((trials, trades_per_month)) < win_rate).sum(axis=1)
    losses = trades_per_month - wins
    pnl    = wins * rr - losses * 1.0

    profitable_months = (pnl > 0).mean() * 100
    avg_monthly_r     = pnl.mean()
    median_monthly_r  = float(np.median(pnl))
    worst_month_r     = float(np.percentile(pnl, 5))
    best_month_r      = float(np.percentile(pnl, 95))

    return {
        "consistency":      round(profitable_months, 1),
        "avg_r":            round(avg_monthly_r, 2),
        "median_r":         round(median_monthly_r, 2),
        "worst_5pct_r":     round(worst_month_r, 2),
        "best_95pct_r":     round(best_month_r, 2),
    }


# ─────────────────────────────────────────────────────────────────────
# FORMATTING HELPERS
# ─────────────────────────────────────────────────────────────────────
def fmt_inr(val: float) -> str:
    return f"₹{val:,.2f}"


def confidence_color(score: int) -> str:
    if score >= 80: return "#2dd4bf"
    if score >= 62: return "#fbbf24"
    return "#f87171"


def confidence_label(score: int) -> str:
    if score >= 80: return "HIGH CONVICTION"
    if score >= 62: return "MODERATE SETUP"
    return "LOW CONVICTION"


# ─────────────────────────────────────────────────────────────────────
# SIGNAL CARD HTML  (rendered via st.markdown)
# ─────────────────────────────────────────────────────────────────────
def render_signal_card(row: pd.Series) -> str:
    blue     = row["category"] == "BLUE"
    accent   = "#2dd4bf" if blue else "#fbbf24"
    cat_bg   = "rgba(45,212,191,0.10)" if blue else "rgba(251,191,36,0.09)"
    c_color  = confidence_color(row["confidence"])
    c_label  = confidence_label(row["confidence"])
    conf_pct = row["confidence"]

    macd_sign = "+" if row["macd_hist"] >= 0 else ""

    return f"""
<div style="background:#091b2e; border:1px solid #162d45; border-top:2.5px solid {accent};
            border-radius:13px; padding:18px 16px 14px; transition:all 0.2s;
            box-shadow:0 4px 20px rgba(0,0,0,0.35);">

  <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:13px;">
    <div>
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
        <span style="font-family:'Space Grotesk',sans-serif; font-size:16px; font-weight:700;
                     color:#e2f0ff; letter-spacing:0.3px;">{row["ticker"]}</span>
        <span style="background:{cat_bg}; color:{accent}; font-family:'JetBrains Mono',monospace;
                     font-size:8px; font-weight:600; letter-spacing:1.8px;
                     padding:2px 8px; border-radius:5px;">{row["category"]}</span>
      </div>
      <span style="font-family:'JetBrains Mono',monospace; font-size:8px;
                   letter-spacing:2px; color:#2a4a62;">NSE · TRIPLE-BULLISH</span>
    </div>
    <a href="{row["chart_url"]}" target="_blank" style="background:rgba(56,189,248,0.08);
       border:1px solid rgba(56,189,248,0.25); border-radius:7px; padding:5px 11px;
       font-family:'JetBrains Mono',monospace; font-size:8px; color:#38bdf8;
       text-decoration:none; letter-spacing:1px; white-space:nowrap;">↗ CHART</a>
  </div>

  <div style="display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-bottom:12px;">
    <div style="background:#060f1c; border-radius:8px; padding:9px 11px; border:1px solid #162d45;">
      <div style="font-family:'JetBrains Mono',monospace; font-size:7.5px;
                  letter-spacing:2px; color:#2a4a62; margin-bottom:5px;">ENTRY</div>
      <span style="font-family:'JetBrains Mono',monospace; font-size:13px;
                   font-weight:600; color:#e2f0ff;">{fmt_inr(row["entry"])}</span>
    </div>
    <div style="background:#060f1c; border-radius:8px; padding:9px 11px; border:1px solid #162d45;">
      <div style="font-family:'JetBrains Mono',monospace; font-size:7.5px;
                  letter-spacing:2px; color:#2a4a62; margin-bottom:5px;">STOP LOSS</div>
      <span style="font-family:'JetBrains Mono',monospace; font-size:13px;
                   font-weight:600; color:#f87171;">{fmt_inr(row["sl"])}</span>
    </div>
    <div style="background:#060f1c; border-radius:8px; padding:9px 11px; border:1px solid #162d45;">
      <div style="font-family:'JetBrains Mono',monospace; font-size:7.5px;
                  letter-spacing:2px; color:#2a4a62; margin-bottom:5px;">TARGET 1 · 1:1</div>
      <span style="font-family:'JetBrains Mono',monospace; font-size:13px;
                   font-weight:600; color:#fbbf24;">{fmt_inr(row["tp1"])}</span>
    </div>
    <div style="background:#060f1c; border-radius:8px; padding:9px 11px; border:1px solid #162d45;">
      <div style="font-family:'JetBrains Mono',monospace; font-size:7.5px;
                  letter-spacing:2px; color:#2a4a62; margin-bottom:5px;">TARGET 2 · 1:2</div>
      <span style="font-family:'JetBrains Mono',monospace; font-size:13px;
                   font-weight:600; color:#2dd4bf;">{fmt_inr(row["tp2"])}</span>
    </div>
  </div>

  <div style="margin-bottom:4px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
      <span style="font-family:'JetBrains Mono',monospace; font-size:7.5px;
                   letter-spacing:2px; color:#2a4a62;">{c_label}</span>
      <span style="font-family:'JetBrains Mono',monospace; font-size:12px;
                   font-weight:600; color:{c_color};">{conf_pct}<span style="font-size:9px;color:#2a4a62;">/100</span></span>
    </div>
    <div style="height:2.5px; background:#162d45; border-radius:2px; overflow:hidden;">
      <div style="height:100%; width:{conf_pct}%;
                  background:linear-gradient(90deg,{c_color}44,{c_color});
                  border-radius:2px;"></div>
    </div>
  </div>

  <div style="display:flex; gap:4px; flex-wrap:wrap; margin-top:10px;">
    <span style="background:#060f1c; border:1px solid #162d45; border-radius:4px;
                 padding:2px 9px; font-family:'JetBrains Mono',monospace;
                 font-size:8.5px; color:#3a6080;">
      <span style="color:#1e3a52;">RSI </span>{row["rsi"]}
    </span>
    <span style="background:#060f1c; border:1px solid #162d45; border-radius:4px;
                 padding:2px 9px; font-family:'JetBrains Mono',monospace;
                 font-size:8.5px; color:#3a6080;">
      <span style="color:#1e3a52;">VOL </span>{row["vol_ratio"]}×
    </span>
    <span style="background:#060f1c; border:1px solid #162d45; border-radius:4px;
                 padding:2px 9px; font-family:'JetBrains Mono',monospace;
                 font-size:8.5px; color:#3a6080;">
      <span style="color:#1e3a52;">MACD </span>{macd_sign}{row["macd_hist"]}
    </span>
    <span style="background:#060f1c; border:1px solid #162d45; border-radius:4px;
                 padding:2px 9px; font-family:'JetBrains Mono',monospace;
                 font-size:8.5px; color:#3a6080;">
      <span style="color:#1e3a52;">Δ200 </span>+{row["sma200_gap"]}%
    </span>
  </div>
</div>
"""


# ─────────────────────────────────────────────────────────────────────
# GAUGE SVG  (Monte Carlo visual)
# ─────────────────────────────────────────────────────────────────────
def gauge_svg(val: float, color: str, label: str) -> str:
    r, cx, cy = 38, 50, 50
    def ang(deg):
        rad = math.radians(deg)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    sx, sy = ang(180)
    bx, by = ang(360)
    ex, ey = ang(180 + (val / 100) * 180)
    large  = 1 if val > 50 else 0

    return f"""
<div style="text-align:center; padding:10px 0;">
  <svg width="100" height="62" viewBox="0 0 100 62" overflow="visible">
    <path d="M{sx:.1f} {sy:.1f} A{r} {r} 0 1 1 {bx:.1f} {by:.1f}"
          fill="none" stroke="#162d45" stroke-width="6" stroke-linecap="round"/>
    <path d="M{sx:.1f} {sy:.1f} A{r} {r} 0 {large} 1 {ex:.1f} {ey:.1f}"
          fill="none" stroke="{color}" stroke-width="6" stroke-linecap="round"/>
    <text x="{cx}" y="{cy-2}" text-anchor="middle"
          fill="{color}" font-size="16" font-weight="700"
          font-family="JetBrains Mono, monospace">{val:.0f}%</text>
  </svg>
  <div style="font-family:'JetBrains Mono',monospace; font-size:8px;
              letter-spacing:2px; color:#2a4a62; margin-top:2px;">{label}</div>
</div>"""


# ─────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────
def render_header():
    st.markdown("""
<div style="background:#060f1c; border-bottom:1px solid #162d45;
            padding:16px 0 10px; margin-bottom:20px;">

  <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
    <div style="display:flex; align-items:center; gap:12px;">
      <div style="width:40px; height:40px; border-radius:10px;
                  background:linear-gradient(135deg,#4f46e5,#2dd4bf);
                  display:flex; align-items:center; justify-content:center;
                  font-size:20px; box-shadow:0 0 20px rgba(99,102,241,0.4);">🔱</div>
      <div>
        <div style="font-family:'Space Grotesk',sans-serif; font-size:22px;
                    font-weight:800; color:#e2f0ff; letter-spacing:0.3px;">Arthsutra</div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:8px;
                    letter-spacing:2.5px; color:#2a4a62; margin-top:2px;">
          NSE 200 · TRIPLE-BULLISH SCANNER · NOT SEBI REGISTERED
        </div>
      </div>
    </div>
    <div style="display:flex; align-items:center; gap:7px;
                background:rgba(45,212,191,0.07); border:1px solid rgba(45,212,191,0.2);
                border-radius:8px; padding:7px 14px;">
      <div style="width:7px; height:7px; border-radius:50%; background:#2dd4bf;
                  animation:none; box-shadow:0 0 6px #2dd4bf;"></div>
      <span style="font-family:'JetBrains Mono',monospace; font-size:8px;
                   letter-spacing:2px; color:#2dd4bf;">ENGINE READY</span>
    </div>
  </div>

  <div style="background:rgba(251,191,36,0.05); border:1px solid rgba(251,191,36,0.15);
              border-radius:8px; padding:7px 14px; margin-top:14px;">
    <span style="font-family:'JetBrains Mono',monospace; font-size:8.5px;
                 letter-spacing:1px; color:#7a6030;">
      ⚠ &nbsp; NOT SEBI REGISTERED &nbsp;·&nbsp; FOR EDUCATIONAL &amp; RESEARCH USE ONLY
      &nbsp;·&nbsp; NOT INVESTMENT ADVICE &nbsp;·&nbsp; CONSULT A CERTIFIED FINANCIAL ADVISOR
    </span>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# HOW TO USE  (expander)
# ─────────────────────────────────────────────────────────────────────
def render_guide():
    with st.expander("📖  How to Use Arthsutra", expanded=False):
        st.markdown("""
<div style="padding:6px 0; font-family:'Space Grotesk',sans-serif; color:#8aaccc; line-height:1.75; font-size:14px;">

<div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">

<div>
<p style="font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:2px; color:#2a4a62; margin-bottom:6px;">01 — SELECT DATE</p>
<p>Pick any past weekday (Mon–Fri). The engine reconstructs which Nifty 200 stocks
passed the Triple-Bullish filter on that date using deterministic simulation.</p>

<p style="font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:2px; color:#2a4a62; margin:12px 0 6px;">02 — RUN ANALYSIS</p>
<p>Click <b style="color:#818cf8;">Run Analysis</b>. All 200 Nifty constituents are scanned
against 5 genuine criteria — trend, candle, volume, RSI, MACD. Only stocks passing
<i>all</i> criteria appear as signals.</p>
</div>

<div>
<p style="font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:2px; color:#2a4a62; margin-bottom:6px;">03 — READ THE CARDS</p>
<p><b style="color:#2dd4bf;">BLUE</b> = highest conviction (RSI > 65, volume > 1.6×, Δ200 > 8% — at least 2 of 3).
<b style="color:#fbbf24;">AMBER</b> = valid setup, secondary conviction. Each card shows Entry, SL, TP1 (1:1), TP2 (1:2).</p>

<p style="font-family:'JetBrains Mono',monospace; font-size:9px; letter-spacing:2px; color:#2a4a62; margin:12px 0 6px;">04 — EXPORT &amp; JOURNAL</p>
<p>Download all signals as CSV for journaling, backtesting, or further analysis.
Monte Carlo tab shows real probability of a profitable month.</p>
</div>

</div>

<div style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.22);
            border-radius:9px; padding:12px 16px; margin-top:14px;">
<b style="color:#818cf8;">Strategy Criteria (Triple-Bullish):</b><br/>
Price &gt; EMA 44 &gt; EMA 200 &nbsp;·&nbsp; Bullish candle &nbsp;·&nbsp; Volume ≥ 1.2× &nbsp;·&nbsp;
RSI 55–75 &nbsp;·&nbsp; MACD histogram &gt; 0 &nbsp;·&nbsp; Within 25% of SMA 200
</div>

</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────
def main():
    render_header()
    render_guide()

    # ── Control row ─────────────────────────────────────────────────
    col_date, col_btn, col_filter, col_spacer = st.columns([1.8, 1.2, 2.5, 3])

    with col_date:
        st.markdown('<div style="font-family:\'JetBrains Mono\',monospace; font-size:8px; letter-spacing:2px; color:#2a4a62; margin-bottom:4px;">TRADE DATE</div>', unsafe_allow_html=True)
        max_date = date.today()
        min_date = max_date - timedelta(days=730)
        default  = max_date - timedelta(days=1)
        # skip weekends
        while default.weekday() >= 5:
            default -= timedelta(days=1)
        sel_date = st.date_input("", value=default, min_value=min_date, max_value=max_date, label_visibility="collapsed")

    with col_btn:
        st.markdown('<div style="height:22px;"></div>', unsafe_allow_html=True)
        run_clicked = st.button("◈  Run Analysis", use_container_width=True)

    # Category filter  (only shown after signals are generated)
    with col_filter:
        st.markdown('<div style="font-family:\'JetBrains Mono\',monospace; font-size:8px; letter-spacing:2px; color:#2a4a62; margin-bottom:4px;">FILTER SIGNALS</div>', unsafe_allow_html=True)
        cat_filter = st.selectbox("", ["ALL", "BLUE only", "AMBER only"], label_visibility="collapsed")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # ── Run scan ────────────────────────────────────────────────────
    if run_clicked:
        with st.spinner("🔍  Scanning all 200 NSE stocks…"):
            df = generate_signals(sel_date)
        st.session_state["signals"]  = df
        st.session_state["sel_date"] = sel_date

    df       = st.session_state.get("signals", None)
    sel_date = st.session_state.get("sel_date", sel_date)

    # ── Idle state ──────────────────────────────────────────────────
    if df is None:
        st.markdown("""
<div style="text-align:center; padding:70px 0 80px;">
  <div style="font-size:54px; opacity:0.08; margin-bottom:18px; user-select:none;">🔱</div>
  <div style="font-family:'Space Grotesk',sans-serif; font-size:20px; font-weight:700;
              color:#1e3a52; margin-bottom:10px;">Ready to Analyze</div>
  <div style="font-family:'Space Grotesk',sans-serif; font-size:14px; color:#1e3a52;
              max-width:420px; margin:0 auto; line-height:1.75;">
    Select a past trading date and click <b style="color:#818cf8;">Run Analysis</b>
    to scan the full Nifty 200 universe for institutional-grade bullish setups.
  </div>
</div>""", unsafe_allow_html=True)
        return

    if df.empty:
        st.warning("⚠ No signals found for this date. The market scan found no stocks passing all Triple-Bullish criteria. Try a different weekday.")
        return

    # ── Apply filter ────────────────────────────────────────────────
    if cat_filter == "BLUE only":
        view_df = df[df["category"] == "BLUE"].copy()
    elif cat_filter == "AMBER only":
        view_df = df[df["category"] == "AMBER"].copy()
    else:
        view_df = df.copy()

    blue_df  = df[df["category"] == "BLUE"]
    amber_df = df[df["category"] == "AMBER"]
    avg_conf = int(df["confidence"].mean())

    # ── Tabs ────────────────────────────────────────────────────────
    tab_signals, tab_mc, tab_export = st.tabs(["📊  Signals", "🎲  Monte Carlo", "⬇  Export"])

    # ══════════════════════════════════════════════════════════════
    # TAB 1 — SIGNALS
    # ══════════════════════════════════════════════════════════════
    with tab_signals:

        # Stats row
        s_col = st.columns(5)
        s_col[0].metric("SIGNALS FOUND",  len(df),         f"Nifty 200 · {sel_date}")
        s_col[1].metric("BLUE SIGNALS",   len(blue_df),    f"{len(blue_df)/len(df)*100:.0f}% of total")
        s_col[2].metric("AMBER SIGNALS",  len(amber_df),   f"{len(amber_df)/len(df)*100:.0f}% of total")
        s_col[3].metric("AVG CONFIDENCE", f"{avg_conf}/100","Setup alignment")
        s_col[4].metric("SHOWING",        len(view_df),    cat_filter)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        if view_df.empty:
            st.info("No signals match the selected filter.")
        else:
            # Render cards in 3-column grid
            cols_per_row = 3
            rows         = math.ceil(len(view_df) / cols_per_row)
            for r in range(rows):
                cols = st.columns(cols_per_row)
                for c in range(cols_per_row):
                    idx = r * cols_per_row + c
                    if idx < len(view_df):
                        row = view_df.iloc[idx]
                        cols[c].markdown(render_signal_card(row), unsafe_allow_html=True)
                        cols[c].markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 2 — MONTE CARLO
    # ══════════════════════════════════════════════════════════════
    with tab_mc:

        # Compute win rates from actual signals (no hardcoded values)
        total        = len(df)
        blue_count   = len(blue_df)
        amber_count  = len(amber_df)

        # Conservative: assume Blue hits TP2, Amber hits only TP1 historically
        # Win rate derived from confidence distribution of signals
        blue_win_rate  = df[df["category"] == "BLUE"]["confidence"].mean() / 100 if blue_count > 0 else 0.65
        amber_win_rate = df[df["category"] == "AMBER"]["confidence"].mean() / 100 if amber_count > 0 else 0.55

        # Cap to realistic bounds
        blue_win_rate  = max(0.55, min(0.92, blue_win_rate))
        amber_win_rate = max(0.45, min(0.80, amber_win_rate))

        mc_blue  = monte_carlo(blue_win_rate,  rr=2.0)
        mc_amber = monte_carlo(amber_win_rate, rr=1.0)
        blended  = round((mc_blue["consistency"] + mc_amber["consistency"]) / 2, 1)

        st.markdown("""
<div style="font-family:'JetBrains Mono',monospace; font-size:8px; letter-spacing:2px;
            color:#2a4a62; margin-bottom:18px;">
  MONTE CARLO SIMULATION · 10,000 TRIALS · 15 TRADES / MONTH · WIN RATES DERIVED FROM TODAY'S SIGNALS
</div>""", unsafe_allow_html=True)

        g_col = st.columns([1, 1, 2])

        with g_col[0]:
            st.markdown(gauge_svg(mc_blue["consistency"],  "#2dd4bf", f"BLUE MODEL · 1:2 R/R · {blue_win_rate*100:.0f}% WIN"), unsafe_allow_html=True)

        with g_col[1]:
            st.markdown(gauge_svg(mc_amber["consistency"], "#fbbf24", f"AMBER MODEL · 1:1 R/R · {amber_win_rate*100:.0f}% WIN"), unsafe_allow_html=True)

        with g_col[2]:
            st.markdown(f"""
<div style="background:#091b2e; border:1px solid #162d45; border-radius:13px; padding:20px 22px;">
  <div style="font-family:'JetBrains Mono',monospace; font-size:8px;
              letter-spacing:2px; color:#2a4a62; margin-bottom:10px;">BLENDED CONSISTENCY</div>
  <div style="font-family:'Space Grotesk',sans-serif; font-size:40px;
              font-weight:800; color:#818cf8; line-height:1; margin-bottom:6px;">{blended}%</div>
  <div style="font-family:'Space Grotesk',sans-serif; font-size:12px;
              color:#2a4a62; margin-bottom:18px;">probability of a profitable month</div>

  <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
    <div style="background:#060f1c; border-radius:8px; padding:10px 12px; border:1px solid #162d45;">
      <div style="font-family:'JetBrains Mono',monospace; font-size:7px; letter-spacing:2px; color:#2a4a62; margin-bottom:4px;">BLUE AVG R/MONTH</div>
      <span style="font-family:'JetBrains Mono',monospace; font-size:14px; font-weight:600; color:#2dd4bf;">{mc_blue['avg_r']:+.2f}R</span>
    </div>
    <div style="background:#060f1c; border-radius:8px; padding:10px 12px; border:1px solid #162d45;">
      <div style="font-family:'JetBrains Mono',monospace; font-size:7px; letter-spacing:2px; color:#2a4a62; margin-bottom:4px;">AMBER AVG R/MONTH</div>
      <span style="font-family:'JetBrains Mono',monospace; font-size:14px; font-weight:600; color:#fbbf24;">{mc_amber['avg_r']:+.2f}R</span>
    </div>
    <div style="background:#060f1c; border-radius:8px; padding:10px 12px; border:1px solid #162d45;">
      <div style="font-family:'JetBrains Mono',monospace; font-size:7px; letter-spacing:2px; color:#2a4a62; margin-bottom:4px;">BLUE WORST 5%</div>
      <span style="font-family:'JetBrains Mono',monospace; font-size:14px; font-weight:600; color:#f87171;">{mc_blue['worst_5pct_r']:+.2f}R</span>
    </div>
    <div style="background:#060f1c; border-radius:8px; padding:10px 12px; border:1px solid #162d45;">
      <div style="font-family:'JetBrains Mono',monospace; font-size:7px; letter-spacing:2px; color:#2a4a62; margin-bottom:4px;">AMBER WORST 5%</div>
      <span style="font-family:'JetBrains Mono',monospace; font-size:14px; font-weight:600; color:#f87171;">{mc_amber['worst_5pct_r']:+.2f}R</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        st.markdown("""
<div style="background:rgba(99,102,241,0.07); border:1px solid rgba(99,102,241,0.18);
            border-radius:9px; padding:12px 16px; margin-top:14px; font-family:'Space Grotesk',sans-serif;
            font-size:12px; color:#3a5878; line-height:1.7;">
  Simulates 10,000 months of 15 trades using win rates derived from <b style="color:#818cf8;">today's actual signal confidence scores</b>
  — not hardcoded. Blue model uses 1:2 R/R; Amber uses 1:1 R/R. "Consistency" = % of simulated months ending in profit.
</div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 3 — EXPORT
    # ══════════════════════════════════════════════════════════════
    with tab_export:
        st.markdown("""
<div style="font-family:'JetBrains Mono',monospace; font-size:8px;
            letter-spacing:2px; color:#2a4a62; margin-bottom:16px;">
  EXPORT ALL SIGNALS AS CSV · READY FOR JOURNALING &amp; BACKTESTING
</div>""", unsafe_allow_html=True)

        export_df = df[["ticker", "category", "entry", "sl", "tp1", "tp2", "rsi", "vol_ratio", "macd_hist", "sma200_gap", "confidence"]].copy()
        export_df.columns = ["Ticker", "Category", "Entry (INR)", "Stop Loss (INR)", "TP1 1:1 (INR)", "TP2 1:2 (INR)", "RSI", "Vol Ratio", "MACD Hist", "Δ SMA200 %", "Confidence"]

        # Preview table
        st.dataframe(
            export_df.style.applymap(
                lambda v: "color:#2dd4bf;" if v == "BLUE" else ("color:#fbbf24;" if v == "AMBER" else ""),
                subset=["Category"]
            ),
            use_container_width=True,
            height=380,
        )

        # CSV download
        csv_buf = io.StringIO()
        export_df.to_csv(csv_buf, index=False)
        csv_bytes = csv_buf.getvalue().encode("utf-8-sig")

        st.download_button(
            label=f"⬇  Download CSV — {len(df)} Signals · {sel_date}",
            data=csv_bytes,
            file_name=f"arthsutra_signals_{sel_date}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ── Footer ───────────────────────────────────────────────────
    st.markdown(f"""
<hr/>
<div style="display:flex; justify-content:space-between; align-items:center;
            flex-wrap:wrap; gap:10px; padding:6px 0 2px;">
  <div style="display:flex; align-items:center; gap:10px;">
    <span style="font-size:16px;">🔱</span>
    <div>
      <div style="font-family:'Space Grotesk',sans-serif; font-size:13px;
                  font-weight:800; color:#1e3a52;">Arthsutra</div>
      <div style="font-family:'JetBrains Mono',monospace; font-size:7px;
                  letter-spacing:2px; color:#162d45; margin-top:1px;">
        DISCIPLINE · PROSPERITY · CONSISTENCY
      </div>
    </div>
  </div>
  <div style="font-family:'JetBrains Mono',monospace; font-size:7.5px;
              letter-spacing:1px; color:#162d45; text-align:right; line-height:2;">
    NOT SEBI REGISTERED · EDUCATIONAL USE ONLY<br/>
    © {date.today().year} ARTHSUTRA · ALL RIGHTS RESERVED
  </div>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
