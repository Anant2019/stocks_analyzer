# ─────────────────────────────────────────────────────────────────────────────
# 12. STREAMLIT UI (INTEGRATED & ERROR-FREE)
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # 1. SIDEBAR CONTROLS
    with st.sidebar:
        st.markdown("## ◈ SYSTEM CONTROLS")
        st.markdown("---")
        
        # AUDIT DATE SELECTOR
        # Defaults to yesterday to ensure data availability
        target_date = st.date_input(
            "AUDIT DATE", 
            datetime.now().date() - timedelta(days=1),
            help="The engine scans price action as of the CLOSE of this date."
        )
        
        st.markdown("---")
        st.markdown("## ⚖️ RISK MODELING")
        trade_count = st.slider("MC TRADES/MONTH", 5, 30, 15)
        
        st.markdown("---")
        st.info("ENGINE STATUS: ONLINE")
        st.caption(f"V3.0.4 | Workers: {cfg.fetch_workers}")

    # 2. TICKER TAPE
    st.markdown(render_ticker_tape(), unsafe_allow_html=True)

    # 3. MAIN DASHBOARD HEADER
    st.markdown(f"""
        <div style="margin-top:20px; margin-bottom:20px;">
            <h1 style='font-family:var(--mono); font-size:28px; letter-spacing:-1px; margin-bottom:0;'>
                ALGO <span style='color:var(--teal)'>ALPHA</span> ENGINE
            </h1>
            <div class='label' style='margin-top:4px;'>
                DATE: {target_date.strftime('%d %b %Y')} &nbsp;·&nbsp; UNIVERSE: NIFTY 200 &nbsp;·&nbsp; SEBI COMPLIANT RESEARCH
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 4. EXECUTION TRIGGER
    if st.button("🚀 INITIATE SYSTEM SCAN", use_container_width=True):
        analyser = Nifty200Analyser()
        
        prog_bar = st.progress(0)
        status_txt = st.empty()
        
        # Core Execution
        signals = analyser.run(target_date, progress_bar=prog_bar, status_text=status_txt)
        
        prog_bar.empty()
        status_txt.empty()

        if not signals:
            st.warning(f"NO QUANT SIGNALS FOUND FOR {target_date}. MARKET REGIME MAY BE NON-TRENDING.")
            return

        # 5. STATS & MONTE CARLO SUMMARY
        jackpots = [s for s in signals if s.status == "JACKPOT"]
        tp1_hits = [s for s in signals if s.status == "TP1_HIT" or s.status == "JACKPOT"]
        
        win_rate_t1 = len(tp1_hits) / len(signals)
        win_rate_t2 = len(jackpots) / len(signals)
        
        # Simulation Logic
        prob_a = monte_carlo(win_rate_t1, 1.0, trades=trade_count)
        prob_b = monte_carlo(win_rate_t2, 2.0, trades=trade_count)

        st.markdown("<div class='section-label'>PROBABILISTIC MODELS</div>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(render_model_card("MODEL ALPHA (1:1)", 1.0, round(win_rate_t1*100), prob_a, "#f5c842"), unsafe_allow_html=True)
        with m2:
            st.markdown(render_model_card("MODEL JACKPOT (1:2)", 2.0, round(win_rate_t2*100), prob_b, "#00d4aa"), unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        
        # 6. SIGNAL GRID
        st.markdown("<div class='section-label'>ACTIVE ALPHA SIGNALS</div>", unsafe_allow_html=True)
        
        cols = st.columns(3)
        for idx, sig in enumerate(signals):
            with cols[idx % 3]:
                st.markdown(render_signal_card(sig), unsafe_allow_html=True)
                
    else:
        # Initial Landing UI
        st.markdown("""
            <div style="background:var(--bg-card); border:1px solid var(--border); padding:60px 20px; text-align:center; border-radius:6px; margin-top:20px;">
                <div class="pulse" style="color:var(--teal); font-family:var(--mono); font-size:10px; letter-spacing:8px; margin-bottom:15px;">SYSTEM STANDBY</div>
                <div class="label">READY TO SCAN NIFTY 200 UNIVERSE</div>
            </div>
        """, unsafe_allow_html=True)

    # 7. SEBI LEGAL FOOTER (Required for Indian Compliance)
    st.markdown("---")
    st.markdown("""
        <div style="font-size: 10px; color: #364f66; font-family: var(--mono); text-align: justify; line-height:1.5;">
            <b>DISCLAIMER:</b> In accordance with SEBI (Research Analysts) Regulations, 2014, please note that this 
            application is a mathematical simulation tool for quantitative research. It does not provide personalized 
            investment advice. The signals generated (BLUE/AMBER) are based on historical technical parameters and 
            do not guarantee future profits. Investing in the stock market involves risk. Please consult a SEBI 
            Registered Investment Advisor before making financial decisions.
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
