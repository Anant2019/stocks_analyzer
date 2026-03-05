# ─────────────────────────────────────────────────────────────────────────────
# 12. STREAMLIT UI (APPENDED LOGIC)
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # 1. SIDEBAR CONTROLS
    with st.sidebar:
        st.markdown("## SYSTEM CONTROLS")
        st.markdown("---")
        
        # FEATURE: Audit Date Selection
        # Allows the user to backtest any specific date in history
        target_date = st.date_input(
            "AUDIT DATE", 
            datetime.now().date() - timedelta(days=1),
            help="Select the date to generate signals for. The system will analyze the close of this day."
        )
        
        st.markdown("---")
        st.markdown("## RISK PARAMETERS")
        trade_count = st.slider("MC TRADES/MONTH", 5, 30, cfg.mc_trades)
        
        st.markdown("---")
        # Global System Status
        st.markdown(f"""
        <div style="border:1px solid #162030; padding:10px; border-radius:5px;">
            <div class="label">CORE ENGINE</div>
            <div class="mono" style="color:#00d4aa; font-size:10px;">V3.0.4-STABLE</div>
            <div class="label" style="margin-top:8px;">FETCH WORKERS</div>
            <div class="mono" style="color:#38bdf8; font-size:10px;">{cfg.fetch_workers} THREADS</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. TICKER TAPE
    st.markdown(render_ticker_tape(), unsafe_allow_html=True)

    # 3. MAIN DASHBOARD HEADER
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"""
            <h1 style='font-family:var(--mono); font-size:28px; letter-spacing:-1px; margin-bottom:0;'>
                ALGO <span style='color:var(--teal)'>ALPHA</span> ENGINE
            </h1>
            <div class='label' style='margin-top:4px;'>AUDIT LOG : {target_date.strftime('%d %b %Y')} · NIFTY 200 UNIVERSE</div>
        """, unsafe_allow_html=True)

    # 4. EXECUTION TRIGGER
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 INITIATE SYSTEM SCAN", use_container_width=True):
        analyser = Nifty200Analyser()
        
        prog_bar = st.progress(0)
        status_txt = st.empty()
        
        # Run Engine
        signals = analyser.run(target_date, progress_bar=prog_bar, status_text=status_txt)
        
        prog_bar.empty()
        status_txt.empty()

        if not signals:
            st.error(f"NO QUANT SIGNALS FOUND FOR {target_date}. MARKET REGIME MAY BE NON-TRENDING.")
            return

        # 5. STATS & MONTE CARLO SUMMARY
        jackpots = [s for s in signals if s.status == "JACKPOT"]
        tp1_hits = [s for s in signals if s.status == "TP1_HIT"]
        
        win_rate_t1 = (len(tp1_hits) + len(jackpots)) / len(signals) if signals else 0
        win_rate_t2 = len(jackpots) / len(signals) if signals else 0
        
        # Monte Carlo Trials
        prob_a = monte_carlo(win_rate_t1, cfg.rr_model_a, trades=trade_count)
        prob_b = monte_carlo(win_rate_t2, cfg.rr_model_b, trades=trade_count)

        st.markdown("<div class='section-label'>PROBABILISTIC MODELS</div>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(render_model_card("MODEL ALPHA (1:1)", cfg.rr_model_a, round(win_rate_t1*100), prob_a, "#f5c842"), unsafe_allow_html=True)
        with m2:
            st.markdown(render_model_card("MODEL JACKPOT (1:2)", cfg.rr_model_b, round(win_rate_t2*100), prob_b, "#00d4aa"), unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # 6. SIGNAL GRID
        st.markdown("<div class='section-label'>ACTIVE ALPHA SIGNALS</div>", unsafe_allow_html=True)
        
        # Displaying in a 3-column responsive grid
        cols = st.columns(3)
        for idx, sig in enumerate(signals):
            with cols[idx % 3]:
                st.markdown(render_signal_card(sig), unsafe_allow_html=True)

    else:
        # Welcome State
        st.info("System Standby. Configure Audit Date in Sidebar and Execute Scan.")
        st.markdown("""
            <div style="background:var(--bg-card); border:1px solid var(--border); padding:40px; text-align:center; border-radius:10px;">
                <div class="mono" style="color:var(--text-lo); font-size:12px; letter-spacing:5px;">AWAITING COMMAND...</div>
            </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
