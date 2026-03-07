"""
N-Queens Solver — Interactive Backtracking Visualizer
======================================================
All original logic preserved exactly:
  ✅ solve_n_queens(n) with board, results, steps
  ✅ is_safe(row, col) — column + both diagonal checks
  ✅ backtrack(row) — full trace with is_backtracking flag
  ✅ Every step recorded with description + board snapshot

Run:  pip install streamlit
      streamlit run n_queens.py
"""

import streamlit as st
import time

# ─────────────────────────────────────────────────────────────────────────────
# CORE ALGORITHM  (original logic, 100% preserved)
# ─────────────────────────────────────────────────────────────────────────────

def solve_n_queens(n):
    board = [['.' for _ in range(n)] for _ in range(n)]
    results = []
    steps = []  # backtracking trace

    def is_safe(row, col):
        # Check column above
        for i in range(row):
            if board[i][col] == 'Q':
                return False
        # Check upper-left diagonal
        for i, j in zip(range(row - 1, -1, -1), range(col - 1, -1, -1)):
            if board[i][j] == 'Q':
                return False
        # Check upper-right diagonal
        for i, j in zip(range(row - 1, -1, -1), range(col + 1, n)):
            if board[i][j] == 'Q':
                return False
        return True

    def backtrack(row):
        steps.append({
            "description": f"Exploring row {row}",
            "board": [r[:] for r in board],
            "is_backtracking": False
        })
        if row == n:
            results.append(["".join(r) for r in board])
            return
        for col in range(n):
            if is_safe(row, col):
                board[row][col] = 'Q'
                backtrack(row + 1)
                board[row][col] = '.'  # Backtrack
                steps.append({
                    "description": f"Backtracking from row {row}, col {col}",
                    "board": [r[:] for r in board],
                    "is_backtracking": True
                })

    backtrack(0)
    return results, steps


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="N-Queens Solver",
    page_icon="♛",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — Aesthetic: Obsidian chess board, ivory accents, monastic precision
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Space+Mono:wght@400;700&family=Nunito:wght@400;600;700&display=swap');

:root {
  --bg:          #0c0c0f;
  --surface:     #13131a;
  --surface2:    #1a1a24;
  --border:      #2a2a3a;
  --border2:     #35355a;
  --gold:        #f0c060;
  --gold-dim:    #b8903a;
  --ivory:       #f5f0e8;
  --ivory-dim:   #c8c0b0;
  --queens:      #f0c060;
  --attack:      rgba(239,68,68,.18);
  --safe:        rgba(52,211,153,.15);
  --backtrack:   rgba(251,146,60,.12);
  --light-sq:    #2a2a3a;
  --dark-sq:     #1a1a24;
  --text-hi:     #f0ece4;
  --text-mid:    #8a8a9a;
  --text-lo:     #4a4a5a;
  --display:     'Playfair Display', serif;
  --mono:        'Space Mono', monospace;
  --body:        'Nunito', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  background: var(--bg) !important;
  font-family: var(--body) !important;
}

.main .block-container {
  padding: 1rem 1rem 4rem !important;
  max-width: 720px !important;
}

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* ── TYPOGRAPHY ── */
.stMarkdown p { color: var(--text-mid) !important; font-size: 14px !important; }
.stMarkdown strong { color: var(--text-hi) !important; }

/* ── SLIDER ── */
[data-testid="stSlider"] {
  padding: 0 !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
  background: var(--gold) !important;
  border-color: var(--gold) !important;
}
[data-testid="stSlider"] div[data-testid="stThumbValue"] {
  color: var(--gold) !important;
  font-family: var(--mono) !important;
}
[data-testid="stSlider"] label {
  color: var(--text-mid) !important;
  font-size: 12px !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
  font-family: var(--mono) !important;
}

/* ── BUTTONS ── */
.stButton > button {
  font-family: var(--body) !important;
  font-weight: 700 !important;
  font-size: 15px !important;
  padding: 12px 20px !important;
  border-radius: 10px !important;
  border: none !important;
  width: 100% !important;
  cursor: pointer !important;
  white-space: nowrap !important;
  transition: all .2s ease !important;
  letter-spacing: 0.3px !important;
}
/* Primary — golden */
div[data-testid="column"]:nth-child(1) .stButton > button,
.primary-btn .stButton > button {
  background: linear-gradient(135deg, #f0c060 0%, #c8893a 100%) !important;
  color: #0c0c0f !important;
}
div[data-testid="column"]:nth-child(1) .stButton > button:hover {
  opacity: .9 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(240,192,96,.25) !important;
}
/* Secondary — slate */
div[data-testid="column"]:nth-child(2) .stButton > button,
div[data-testid="column"]:nth-child(3) .stButton > button {
  background: linear-gradient(135deg, #2a2a3a 0%, #1a1a24 100%) !important;
  color: var(--ivory-dim) !important;
  border: 1.5px solid var(--border2) !important;
}
div[data-testid="column"]:nth-child(2) .stButton > button:hover,
div[data-testid="column"]:nth-child(3) .stButton > button:hover {
  border-color: var(--gold-dim) !important;
  color: var(--gold) !important;
  transform: translateY(-1px) !important;
}
/* Disabled */
.stButton > button:disabled {
  opacity: .35 !important;
  cursor: not-allowed !important;
  transform: none !important;
}

/* ── SELECT BOX ── */
[data-testid="stSelectbox"] > div > div {
  background: var(--surface2) !important;
  border: 1.5px solid var(--border2) !important;
  border-radius: 10px !important;
  color: var(--text-hi) !important;
  font-family: var(--body) !important;
  font-size: 14px !important;
}
[data-testid="stSelectbox"] label {
  color: var(--text-mid) !important;
  font-size: 11px !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
  font-family: var(--mono) !important;
}

/* ── PROGRESS ── */
[data-testid="stProgress"] > div > div {
  background: linear-gradient(90deg, var(--gold-dim), var(--gold)) !important;
}

/* ── EXPANDERS ── */
[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  margin-bottom: 10px !important;
}
[data-testid="stExpander"] summary {
  color: var(--text-mid) !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  padding: 12px 16px !important;
  font-family: var(--body) !important;
}

/* ── METRICS ── */
[data-testid="metric-container"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 14px 12px !important;
  text-align: center !important;
}
[data-testid="metric-container"] label {
  color: var(--text-lo) !important;
  font-size: 10px !important;
  font-family: var(--mono) !important;
  letter-spacing: 1.5px !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
  color: var(--gold) !important;
  font-family: var(--mono) !important;
  font-size: 26px !important;
  font-weight: 700 !important;
}

hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# BOARD RENDERER  — HTML chess board
# ─────────────────────────────────────────────────────────────────────────────

def render_board_html(board_state: list, n: int, is_bt: bool = False, highlight_queens: bool = True) -> str:
    """Render board as an HTML table with chess colouring."""
    
    # Compute attacked squares
    queen_positions = [(r, c) for r in range(n) for c in range(n) if board_state[r][c] == 'Q']
    attacked = set()
    for qr, qc in queen_positions:
        for r in range(n):
            attacked.add((r, qc))          # column
        for d in range(1, n):
            for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                nr, nc = qr+dr*d, qc+dc*d
                if 0 <= nr < n and 0 <= nc < n:
                    attacked.add((nr, nc))

    cell_size = max(44, min(68, 380 // n))
    font_size = cell_size * 0.58

    header_bg = "rgba(251,146,60,.08)" if is_bt else "rgba(52,211,153,.06)"
    header_border = "#fb923c44" if is_bt else "#34d39944"
    header_txt = "#fb923c" if is_bt else "#34d399"
    header_icon = "↩ BACKTRACKING" if is_bt else "→ PLACING"

    rows_html = ""
    for r in range(n):
        cells = ""
        for c in range(n):
            is_light = (r + c) % 2 == 0
            base_bg  = "#2c2c3c" if is_light else "#1c1c28"
            has_queen = board_state[r][c] == 'Q'
            is_attacked = (r, c) in attacked and not has_queen

            if has_queen:
                bg = "#3a3010" if is_light else "#2a2208"
                border = "2px solid rgba(240,192,96,.6)"
                content = f'<span style="font-size:{font_size}px;line-height:1;filter:drop-shadow(0 2px 6px rgba(240,192,96,.5));">♛</span>'
            elif is_attacked:
                bg = "rgba(239,68,68,.12)" if not is_light else "rgba(239,68,68,.08)"
                border = "1px solid rgba(239,68,68,.15)"
                content = f'<span style="color:rgba(239,68,68,.25);font-size:{int(font_size*0.4)}px;">✕</span>'
            else:
                bg = base_bg
                border = "1px solid transparent"
                content = ""

            cells += f"""<td style="width:{cell_size}px;height:{cell_size}px;
                background:{bg};border:{border};
                text-align:center;vertical-align:middle;
                transition:background .2s;">{content}</td>"""
        rows_html += f"<tr>{cells}</tr>"

    col_labels = "".join(
        f'<td style="width:{cell_size}px;text-align:center;color:#3a3a4a;'
        f'font-size:10px;font-family:var(--mono);padding-bottom:3px;">{chr(65+c)}</td>'
        for c in range(n)
    )
    row_labels_map = {r: f'<td style="padding-right:5px;color:#3a3a4a;font-size:10px;'
                        f'font-family:var(--mono);text-align:right;vertical-align:middle;">{n-r}</td>'
                      for r in range(n)}

    full_rows = ""
    for r, row_html in enumerate(rows_html.split("</tr>")):
        if row_html.strip():
            full_rows += f"<tr>{row_labels_map[r]}{row_html.replace('<tr>','')}</tr>"

    return f"""
<div style="background:{header_bg};border:1px solid {header_border};
            border-radius:8px;padding:6px 12px;margin-bottom:10px;
            display:inline-block;">
  <span style="color:{header_txt};font-family:var(--mono);font-size:10px;
               letter-spacing:1.5px;font-weight:700;">{header_icon}</span>
</div>
<div style="overflow-x:auto;">
  <table style="border-collapse:collapse;border-radius:10px;overflow:hidden;
                border:1px solid #2a2a3a;margin:0 auto;display:block;width:fit-content;">
    <thead>
      <tr>
        <td style="width:20px;"></td>{col_labels}
      </tr>
    </thead>
    <tbody>{full_rows}</tbody>
  </table>
</div>
"""


def render_solution_board(solution_rows: list, n: int, idx: int) -> str:
    """Render a complete solution board (no attacks shown, all queens placed)."""
    cell_size = max(36, min(56, 340 // n))
    font_size = cell_size * 0.58

    rows_html = ""
    for r, row_str in enumerate(solution_rows):
        cells = ""
        for c, ch in enumerate(row_str):
            is_light = (r + c) % 2 == 0
            has_queen = ch == 'Q'
            if has_queen:
                bg = "#3a3010" if is_light else "#2a2208"
                border = "2px solid rgba(240,192,96,.5)"
                content = f'<span style="font-size:{font_size}px;line-height:1;">♛</span>'
            else:
                bg = "#2c2c3c" if is_light else "#1c1c28"
                border = "1px solid transparent"
                content = ""
            cells += f'<td style="width:{cell_size}px;height:{cell_size}px;background:{bg};border:{border};text-align:center;vertical-align:middle;">{content}</td>'
        rows_html += f"<tr>{cells}</tr>"

    return f"""
<div style="background:var(--surface);border:1px solid var(--border);
            border-top:2px solid rgba(240,192,96,.4);border-radius:10px;
            padding:14px;margin-bottom:10px;text-align:center;">
  <div style="color:var(--text-lo);font-family:var(--mono);font-size:10px;
              letter-spacing:2px;margin-bottom:10px;">SOLUTION #{idx+1}</div>
  <div style="overflow-x:auto;">
    <table style="border-collapse:collapse;margin:0 auto;display:block;width:fit-content;
                  border:1px solid #2a2a3a;border-radius:8px;overflow:hidden;">
      <tbody>{rows_html}</tbody>
    </table>
  </div>
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "results": None,
        "steps": None,
        "step_idx": 0,
        "n": 6,
        "playing": False,
        "solved": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 2.5rem 0 1.5rem; text-align: center; position: relative;">
  <!-- decorative line -->
  <div style="position:absolute;top:0;left:50%;transform:translateX(-50%);
              width:60px;height:3px;background:linear-gradient(90deg,transparent,#f0c060,transparent);
              border-radius:2px;"></div>
  
  <div style="font-size:48px;margin-bottom:8px;filter:drop-shadow(0 4px 12px rgba(240,192,96,.3));">♛</div>
  <h1 style="font-family:'Playfair Display',serif;font-size:32px;font-weight:800;
             color:#f0ece4;margin:0 0 6px;letter-spacing:-0.5px;">
    N-Queens Solver
  </h1>
  <p style="color:#4a4a5a;font-family:'Space Mono',monospace;font-size:11px;
            letter-spacing:3px;margin:0;text-transform:uppercase;">
    Backtracking Visualizer
  </p>
</div>

<!-- thin rule -->
<div style="height:1px;background:linear-gradient(90deg,transparent,#2a2a3a,transparent);
            margin-bottom:1.5rem;"></div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CONTROLS CARD
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:16px;
            padding:22px 20px 18px;margin-bottom:1.2rem;">
  <div style="color:#4a4a5a;font-family:'Space Mono',monospace;font-size:10px;
              letter-spacing:2px;margin-bottom:14px;">CONFIGURATION</div>
""", unsafe_allow_html=True)

col_n, col_info = st.columns([3, 2])
with col_n:
    n_val = st.slider(
        "Board size (N)",
        min_value=4, max_value=10,
        value=st.session_state["n"],
        key="n_slider",
        help="N queens on an N×N board"
    )
with col_info:
    # Show quick stats for chosen N
    known = {4:2, 5:10, 6:4, 7:40, 8:92, 9:352, 10:724}
    sol_count = known.get(n_val, "?")
    st.markdown(f"""
<div style="background:#1a1a24;border:1px solid #2a2a3a;border-radius:10px;
            padding:12px 14px;margin-top:24px;">
  <div style="color:#4a4a5a;font-size:10px;font-family:'Space Mono',monospace;
              letter-spacing:1.5px;margin-bottom:4px;">KNOWN SOLUTIONS</div>
  <div style="color:#f0c060;font-size:28px;font-weight:700;
              font-family:'Space Mono',monospace;">{sol_count}</div>
  <div style="color:#3a3a4a;font-size:10px;font-family:'Space Mono',monospace;">
    for N = {n_val}
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ACTION BUTTONS
# ─────────────────────────────────────────────────────────────────────────────
btn_c1, btn_c2, btn_c3 = st.columns(3)

with btn_c1:
    solve_clicked = st.button("♛  Solve & Visualize", key="solve_btn")
with btn_c2:
    prev_clicked = st.button("← Prev Step", key="prev_btn",
                             disabled=(st.session_state["steps"] is None or st.session_state["step_idx"] == 0))
with btn_c3:
    next_clicked = st.button("Next Step →", key="next_btn",
                             disabled=(st.session_state["steps"] is None or
                                       st.session_state["step_idx"] >= len(st.session_state["steps"]) - 1))

# ─────────────────────────────────────────────────────────────────────────────
# HANDLE BUTTON ACTIONS
# ─────────────────────────────────────────────────────────────────────────────
if solve_clicked:
    st.session_state["n"] = n_val
    with st.spinner("Running backtracking algorithm…"):
        results, steps = solve_n_queens(n_val)
    st.session_state["results"] = results
    st.session_state["steps"]   = steps
    st.session_state["step_idx"] = 0
    st.session_state["solved"]  = True
    st.rerun()

if prev_clicked and st.session_state["steps"]:
    st.session_state["step_idx"] = max(0, st.session_state["step_idx"] - 1)

if next_clicked and st.session_state["steps"]:
    st.session_state["step_idx"] = min(
        len(st.session_state["steps"]) - 1,
        st.session_state["step_idx"] + 1
    )


# ─────────────────────────────────────────────────────────────────────────────
# VISUALIZER
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state["steps"] is not None:
    steps   = st.session_state["steps"]
    results = st.session_state["results"]
    idx     = st.session_state["step_idx"]
    n       = st.session_state["n"]
    step    = steps[idx]

    st.markdown("---")

    # ── Progress bar & step counter ──────────────────────────────────────────
    progress = (idx + 1) / len(steps)
    st.progress(progress)

    # Stats row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Step", f"{idx + 1}")
    m2.metric("Total Steps", f"{len(steps)}")
    m3.metric("Solutions", f"{len(results)}")
    m4.metric("Progress", f"{int(progress*100)}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step description card ─────────────────────────────────────────────────
    is_bt  = step["is_backtracking"]
    desc   = step["description"]
    desc_bg     = "rgba(251,146,60,.06)" if is_bt else "rgba(52,211,153,.05)"
    desc_border = "#fb923c44"            if is_bt else "#34d39944"
    desc_color  = "#fb923c"             if is_bt else "#34d399"
    desc_icon   = "↩"                   if is_bt else "→"

    st.markdown(f"""
<div style="background:{desc_bg};border:1px solid {desc_border};
            border-left:3px solid {desc_color};
            border-radius:10px;padding:14px 18px;margin-bottom:16px;">
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="font-size:18px;">{desc_icon}</span>
    <div>
      <div style="color:{desc_color};font-family:'Space Mono',monospace;
                  font-size:11px;letter-spacing:1.5px;margin-bottom:3px;">
        {'BACKTRACKING' if is_bt else 'FORWARD EXPLORATION'}
      </div>
      <div style="color:#c8c0b0;font-family:'Nunito',sans-serif;font-size:14px;font-weight:600;">
        {desc}
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Board ─────────────────────────────────────────────────────────────────
    st.markdown(
        render_board_html(step["board"], n, is_bt),
        unsafe_allow_html=True
    )

    # ── Legend ────────────────────────────────────────────────────────────────
    st.markdown("""
<div style="display:flex;gap:16px;justify-content:center;margin:12px 0 8px;flex-wrap:wrap;">
  <span style="color:#4a4a5a;font-size:11px;font-family:'Space Mono',monospace;display:flex;align-items:center;gap:5px;">
    <span style="font-size:14px;">♛</span> Queen placed
  </span>
  <span style="color:#4a4a5a;font-size:11px;font-family:'Space Mono',monospace;display:flex;align-items:center;gap:5px;">
    <span style="color:rgba(239,68,68,.5);">✕</span> Under attack
  </span>
  <span style="color:#34d399;font-size:11px;font-family:'Space Mono',monospace;">→ Forward</span>
  <span style="color:#fb923c;font-size:11px;font-family:'Space Mono',monospace;">↩ Backtrack</span>
</div>
""", unsafe_allow_html=True)

    # ── Step navigation slider ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    new_idx = st.slider(
        "Jump to step",
        min_value=0,
        max_value=len(steps) - 1,
        value=idx,
        key="step_slider",
    )
    if new_idx != idx:
        st.session_state["step_idx"] = new_idx
        st.rerun()

    st.markdown("---")

    # ─────────────────────────────────────────────────────────────────────────
    # SOLUTIONS PANEL
    # ─────────────────────────────────────────────────────────────────────────
    if results:
        with st.expander(f"♛  View All {len(results)} Solutions", expanded=False):
            # Solution selector
            sol_opts = [f"Solution {i+1}" for i in range(len(results))]
            chosen_sol = st.selectbox("Choose solution", sol_opts, key="sol_select")
            sol_idx    = sol_opts.index(chosen_sol)

            st.markdown(
                render_solution_board(results[sol_idx], n, sol_idx),
                unsafe_allow_html=True
            )

            # Board as string representation
            st.markdown(f"""
<div style="background:#1a1a24;border:1px solid #2a2a3a;border-radius:8px;
            padding:12px 16px;margin-top:10px;">
  <div style="color:#3a3a4a;font-family:'Space Mono',monospace;font-size:10px;
              letter-spacing:1.5px;margin-bottom:8px;">TEXT REPRESENTATION</div>
  <pre style="color:#f0c060;font-family:'Space Mono',monospace;font-size:14px;
              line-height:1.8;margin:0;letter-spacing:4px;">{"<br>".join(results[sol_idx])}</pre>
</div>
""", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # BACKTRACKING STATISTICS
    # ─────────────────────────────────────────────────────────────────────────
    with st.expander("📊  Algorithm Statistics", expanded=False):
        forward_steps = sum(1 for s in steps if not s["is_backtracking"])
        back_steps    = sum(1 for s in steps if s["is_backtracking"])
        efficiency    = round(len(results) / len(steps) * 100, 2) if steps else 0

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Forward",     forward_steps)
        sc2.metric("Backtracks",  back_steps)
        sc3.metric("Solutions",   len(results))
        sc4.metric("Efficiency",  f"{efficiency}%", help="Solutions per 100 steps")

        # Step type breakdown
        st.markdown(f"""
<div style="background:#1a1a24;border:1px solid #2a2a3a;border-radius:10px;
            padding:14px 16px;margin-top:12px;">
  <div style="color:#3a3a4a;font-family:'Space Mono',monospace;font-size:10px;
              letter-spacing:1.5px;margin-bottom:10px;">STEP BREAKDOWN</div>
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
    <div style="flex:1;height:8px;background:#1c1c28;border-radius:4px;overflow:hidden;">
      <div style="height:100%;width:{round(forward_steps/len(steps)*100)}%;
                  background:linear-gradient(90deg,#34d39966,#34d399);border-radius:4px;"></div>
    </div>
    <span style="color:#34d399;font-family:'Space Mono',monospace;font-size:11px;min-width:80px;">
      {forward_steps} forward
    </span>
  </div>
  <div style="display:flex;gap:8px;align-items:center;">
    <div style="flex:1;height:8px;background:#1c1c28;border-radius:4px;overflow:hidden;">
      <div style="height:100%;width:{round(back_steps/len(steps)*100)}%;
                  background:linear-gradient(90deg,#fb923c66,#fb923c);border-radius:4px;"></div>
    </div>
    <span style="color:#fb923c;font-family:'Space Mono',monospace;font-size:11px;min-width:80px;">
      {back_steps} backtracks
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # HOW IT WORKS (algorithm explanation)
    # ─────────────────────────────────────────────────────────────────────────
    with st.expander("📖  How the Algorithm Works", expanded=False):
        st.markdown("""
### N-Queens Problem

Place **N queens** on an **N×N chessboard** so no two queens attack each other.
Two queens attack each other if they share the **same row**, **column**, or **diagonal**.

---

### Backtracking Strategy

The algorithm works **row by row** (row 0 → row N−1):

**`is_safe(row, col)`** checks three directions above the candidate cell:
1. **Column** — scans straight up
2. **Upper-left diagonal** — scans up-left
3. **Upper-right diagonal** — scans up-right

**`backtrack(row)`** tries every column in the current row:
- If placing a queen at `(row, col)` is safe → place it, recurse to `row+1`
- If `row == N` → all queens placed, record solution
- After recursing → **remove** the queen (`board[row][col] = '.'`) and try next column

Every placement and removal is recorded as a **step** with a board snapshot.

---

### Complexity

| | Value |
|---|---|
| Time (worst case) | O(N!) |
| Space | O(N²) |
| Solutions for N=8 | 92 |
| Solutions for N=10 | 724 |

---

### Step Colours
- **🟢 Green** → Forward: placing a queen, exploring deeper
- **🟠 Orange** → Backtrack: removing a queen, trying next column
- **✕ Red squares** → Currently under attack by a placed queen
""")

    # ─────────────────────────────────────────────────────────────────────────
    # STEP LOG  — full trace
    # ─────────────────────────────────────────────────────────────────────────
    with st.expander(f"📋  Full Step Log ({len(steps)} steps)", expanded=False):
        # Group and display last 50 steps around current position
        window = 25
        start  = max(0, idx - window)
        end    = min(len(steps), idx + window + 1)

        log_rows = ""
        for i in range(start, end):
            s     = steps[i]
            is_current = i == idx
            row_bg = "rgba(240,192,96,.08)" if is_current else "transparent"
            row_bdr= "1px solid rgba(240,192,96,.3)" if is_current else "1px solid transparent"
            num_color = "#f0c060" if is_current else "#3a3a4a"
            desc_color = "#f0ece4" if is_current else ("#fb923c" if s["is_backtracking"] else "#8a8a9a")
            type_color = "#fb923c" if s["is_backtracking"] else "#34d399"
            type_label = "↩ BT" if s["is_backtracking"] else "→ FW"

            log_rows += f"""
<div style="display:grid;grid-template-columns:40px 55px 1fr;gap:8px;align-items:center;
            padding:7px 10px;border-radius:6px;background:{row_bg};border:{row_bdr};
            margin-bottom:2px;">
  <span style="color:{num_color};font-family:'Space Mono',monospace;font-size:11px;">{i+1}</span>
  <span style="color:{type_color};font-family:'Space Mono',monospace;font-size:10px;
               letter-spacing:1px;">{type_label}</span>
  <span style="color:{desc_color};font-size:12px;font-family:'Nunito',sans-serif;">{s['description']}</span>
</div>"""

        st.markdown(f"""
<div style="background:#13131a;border:1px solid #2a2a3a;border-radius:10px;
            padding:12px;max-height:380px;overflow-y:auto;">
  <div style="color:#3a3a4a;font-family:'Space Mono',monospace;font-size:10px;
              letter-spacing:1.5px;margin-bottom:10px;">
    SHOWING STEPS {start+1}–{end} (CURRENT: {idx+1})
  </div>
  {log_rows}
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE  (before first solve)
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.markdown("""
<div style="text-align:center;padding:3rem 1rem;color:#2a2a3a;">
  <div style="font-size:64px;margin-bottom:16px;opacity:.4;
              filter:grayscale(1);">♛</div>
  <div style="color:#3a3a4a;font-family:'Space Mono',monospace;font-size:13px;
              letter-spacing:2px;text-transform:uppercase;">
    Set N and click Solve to begin
  </div>
  <div style="color:#2a2a3a;font-size:12px;margin-top:8px;font-family:'Space Mono',monospace;">
    Watch backtracking unfold step by step
  </div>
</div>
""", unsafe_allow_html=True)

    # Explain the problem before first solve
    with st.expander("📖  What is the N-Queens problem?", expanded=True):
        st.markdown("""
Place **N queens** on an N×N chessboard so that no two queens attack each other.

Queens attack along **rows**, **columns**, and **diagonals** — so every queen must be in a unique row, column, and diagonal.

**How this solver works:**

1. Try placing a queen in each column of row 0
2. For each valid placement, move to row 1 and repeat
3. If no column in a row is safe → **backtrack** (remove the last queen and try the next column)
4. Continue until all rows have a queen placed → **solution found**

Use the **Prev / Next** buttons to step through every decision the algorithm makes.
""")


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 0.5rem;
            border-top:1px solid #1c1c28;margin-top:2rem;">
  <span style="color:#2a2a3a;font-family:'Space Mono',monospace;font-size:10px;
               letter-spacing:2px;">
    N-QUEENS · BACKTRACKING ALGORITHM · ALL LOGIC PRESERVED
  </span>
</div>
""", unsafe_allow_html=True)
