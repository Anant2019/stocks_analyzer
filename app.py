"""
NSE 200 Swing Trade Screener
Python conversion of the React Index component
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import random
from datetime import datetime
from dataclasses import dataclass
from typing import List

# ─────────────────────────────────────────────
# DATA: NSE 200 Stocks (sample subset)
# ─────────────────────────────────────────────
NSE_200_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "BAJFINANCE", "KOTAKBANK",
    "LT", "ASIANPAINT", "AXISBANK", "MARUTI", "SUNPHARMA",
    "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO", "POWERGRID",
    "NTPC", "TECHM", "HCLTECH", "BAJAJFINSV", "ONGC",
    "TATAMOTORS", "ADANIPORTS", "DIVISLAB", "DRREDDY", "CIPLA",
    "JSWSTEEL", "TATASTEEL", "HINDALCO", "COALINDIA", "IOC",
    "BPCL", "GRASIM", "EICHERMOT", "HEROMOTOCO", "BRITANNIA",
    "SHREECEM", "INDUSINDBK", "M&M", "BAJAJ-AUTO", "SIEMENS",
    "PIDILITIND", "DABUR", "GODREJCP", "MARICO", "COLPAL",
]

# ─────────────────────────────────────────────
# DATA MODEL
# ─────────────────────────────────────────────
@dataclass
class ScreenerResult:
    symbol: str
    signal: str        # "BUY" / "WATCH"
    rsi: float
    macd: str          # "Bullish" / "Neutral"
    above_ema: bool
    volume_surge: bool
    score: int         # 0-100


# ─────────────────────────────────────────────
# DEMO DATA GENERATOR
# ─────────────────────────────────────────────
def generate_demo_data() -> List[ScreenerResult]:
    results = []
    candidates = random.sample(NSE_200_STOCKS, k=random.randint(8, 18))
    for sym in candidates:
        rsi = round(random.uniform(45, 70), 1)
        macd = random.choice(["Bullish", "Neutral"])
        above_ema = random.random() > 0.3
        volume_surge = random.random() > 0.4
        score = int(
            (rsi / 100) * 40
            + (20 if macd == "Bullish" else 0)
            + (20 if above_ema else 0)
            + (20 if volume_surge else 0)
        )
        signal = "BUY" if score >= 60 else "WATCH"
        results.append(ScreenerResult(sym, signal, rsi, macd, above_ema, volume_surge, score))
    results.sort(key=lambda r: r.score, reverse=True)
    return results


# ─────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────
class NSEScreenerApp:
    # ── Colour palette ──────────────────────
    BG        = "#0f1117"
    SURFACE   = "#1a1d27"
    BORDER    = "#2a2d3a"
    TEXT      = "#e2e8f0"
    MUTED     = "#64748b"
    PRIMARY   = "#3b82f6"
    BULLISH   = "#22c55e"
    WATCH     = "#f59e0b"
    ACCENT    = "#6366f1"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("NSE 200 Swing Screener")
        self.root.geometry("960x660")
        self.root.configure(bg=self.BG)
        self.root.resizable(True, True)

        self.results: List[ScreenerResult] = []
        self.is_scanning = False
        self.has_scanned = False
        self.show_strategy = tk.BooleanVar(value=False)

        self._build_ui()

    # ── UI BUILD ────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_toolbar()
        self._build_strategy_panel()
        self._build_table()
        self._build_empty_state()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=self.SURFACE, pady=12)
        hdr.pack(fill="x")

        tk.Label(
            hdr, text="⬆  NSE Swing Screener",
            bg=self.SURFACE, fg=self.TEXT,
            font=("Courier New", 16, "bold")
        ).pack(side="left", padx=16)

        self.stats_label = tk.Label(
            hdr, text=f"Scanning {len(NSE_200_STOCKS)} stocks",
            bg=self.SURFACE, fg=self.MUTED,
            font=("Courier New", 10)
        )
        self.stats_label.pack(side="left", padx=8)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            hdr, variable=self.progress_var,
            length=180, mode="determinate",
            style="Accent.Horizontal.TProgressbar"
        )
        # shown only while scanning
        self._style_progressbar()

    def _style_progressbar(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=self.BORDER,
            background=self.PRIMARY,
            thickness=6
        )

    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg=self.BG, pady=10)
        bar.pack(fill="x", padx=16)

        self.scan_btn = tk.Button(
            bar, text="▶  Scan Now",
            command=self._on_scan,
            bg=self.PRIMARY, fg="white",
            activebackground="#2563eb", activeforeground="white",
            font=("Courier New", 11, "bold"),
            relief="flat", padx=18, pady=8, cursor="hand2"
        )
        self.scan_btn.pack(side="left")

        self.strat_btn = tk.Button(
            bar, text="ℹ  Strategy",
            command=self._toggle_strategy,
            bg=self.SURFACE, fg=self.TEXT,
            activebackground=self.BORDER, activeforeground=self.TEXT,
            font=("Courier New", 11),
            relief="flat", padx=18, pady=8, cursor="hand2"
        )
        self.strat_btn.pack(side="left", padx=10)

        self.scan_time_label = tk.Label(
            bar, text="", bg=self.BG, fg=self.MUTED,
            font=("Courier New", 9)
        )
        self.scan_time_label.pack(side="right")

    def _build_strategy_panel(self):
        self.strategy_frame = tk.Frame(
            self.root, bg=self.SURFACE,
            padx=20, pady=14
        )
        # not packed yet — shown on toggle

        title = tk.Label(
            self.strategy_frame, text="Strategy: Swing Buy Signal",
            bg=self.SURFACE, fg=self.TEXT,
            font=("Courier New", 12, "bold")
        )
        title.pack(anchor="w")

        criteria = [
            "RSI between 40–70 (momentum, not overbought)",
            "MACD bullish crossover or positive histogram",
            "Price above 20-day EMA (uptrend filter)",
            "Volume 1.5× 20-day average (institutional interest)",
        ]
        for c in criteria:
            tk.Label(
                self.strategy_frame, text=f"  • {c}",
                bg=self.SURFACE, fg=self.MUTED,
                font=("Courier New", 10)
            ).pack(anchor="w", pady=1)

        tk.Label(
            self.strategy_frame,
            text="⚠  Demo data only · Connect live API for real signals",
            bg=self.SURFACE, fg=self.WATCH,
            font=("Courier New", 9)
        ).pack(anchor="w", pady=(8, 0))

    def _build_table(self):
        wrapper = tk.Frame(self.root, bg=self.BG, padx=16, pady=6)
        wrapper.pack(fill="both", expand=True)

        cols = ("symbol", "signal", "rsi", "macd", "above_ema", "vol_surge", "score")
        headers = ("Symbol", "Signal", "RSI", "MACD", "Above EMA", "Vol Surge", "Score")

        style = ttk.Style()
        style.configure(
            "Dark.Treeview",
            background=self.SURFACE,
            foreground=self.TEXT,
            fieldbackground=self.SURFACE,
            borderwidth=0,
            rowheight=28,
            font=("Courier New", 10)
        )
        style.configure(
            "Dark.Treeview.Heading",
            background=self.BORDER,
            foreground=self.MUTED,
            font=("Courier New", 10, "bold"),
            relief="flat"
        )
        style.map("Dark.Treeview", background=[("selected", self.ACCENT)])

        self.tree = ttk.Treeview(
            wrapper, columns=cols, show="headings",
            style="Dark.Treeview"
        )
        for col, hdr in zip(cols, headers):
            self.tree.heading(col, text=hdr)
        widths = [100, 80, 70, 90, 90, 90, 70]
        for col, w in zip(cols, widths):
            self.tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(wrapper, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # Tag colours
        self.tree.tag_configure("buy",   foreground=self.BULLISH)
        self.tree.tag_configure("watch", foreground=self.WATCH)

    def _build_empty_state(self):
        self.empty_frame = tk.Frame(self.root, bg=self.BG, pady=24)
        self.empty_frame.pack(fill="x")

        tk.Label(
            self.empty_frame, text="▶",
            bg=self.BG, fg=self.BULLISH,
            font=("Courier New", 28)
        ).pack()
        tk.Label(
            self.empty_frame, text="Ready to Scan",
            bg=self.BG, fg=self.TEXT,
            font=("Courier New", 14, "bold")
        ).pack(pady=(4, 0))
        tk.Label(
            self.empty_frame, text="Analyze NSE 200 stocks for swing buy signals",
            bg=self.BG, fg=self.MUTED,
            font=("Courier New", 10)
        ).pack()
        tk.Label(
            self.empty_frame,
            text="Currently showing demo data · Connect live API for real-time screening",
            bg=self.BG, fg=self.MUTED,
            font=("Courier New", 9)
        ).pack(pady=(6, 0))

    # ── ACTIONS ─────────────────────────────
    def _toggle_strategy(self):
        if self.show_strategy.get():
            self.strategy_frame.pack_forget()
            self.show_strategy.set(False)
        else:
            self.strategy_frame.pack(fill="x", padx=16, pady=(0, 6))
            self.show_strategy.set(True)

    def _on_scan(self):
        if self.is_scanning:
            return
        self.is_scanning = True
        self.has_scanned = True
        self.scan_btn.configure(text="⏳  Scanning...", state="disabled")
        self.empty_frame.pack_forget()

        # clear table
        for row in self.tree.get_children():
            self.tree.delete(row)

        # show progress bar in header
        hdr_frame = self.root.winfo_children()[0]
        self.progress_bar.pack(side="right", padx=16)

        thread = threading.Thread(target=self._scan_worker, daemon=True)
        thread.start()

    def _scan_worker(self):
        for i in range(0, 101, 5):
            time.sleep(0.06)
            self.root.after(0, self._update_progress, i)
        demo = generate_demo_data()
        self.root.after(0, self._finish_scan, demo)

    def _update_progress(self, value: int):
        self.progress_var.set(value)
        self.stats_label.configure(
            text=f"Scanning {len(NSE_200_STOCKS)} stocks … {value}%"
        )

    def _finish_scan(self, results: List[ScreenerResult]):
        self.results = results
        self.is_scanning = False

        # populate table
        for r in results:
            tag = "buy" if r.signal == "BUY" else "watch"
            self.tree.insert("", "end", values=(
                r.symbol,
                r.signal,
                f"{r.rsi:.1f}",
                r.macd,
                "✔" if r.above_ema else "✘",
                "✔" if r.volume_surge else "✘",
                r.score,
            ), tags=(tag,))

        # update UI
        self.scan_btn.configure(text="▶  Scan Now", state="normal")
        self.stats_label.configure(
            text=f"{len(NSE_200_STOCKS)} stocks · {len(results)} matches"
        )
        self.progress_bar.pack_forget()
        self.scan_time_label.configure(
            text=f"Last scan: {datetime.now().strftime('%H:%M:%S')} · Demo data"
        )


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = NSEScreenerApp(root)
    root.mainloop()
