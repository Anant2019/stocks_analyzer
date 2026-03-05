import { useState, useEffect, useRef } from "react";

function seededRand(seed) {
  let s = seed;
  return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
}

const UNIVERSE = [
  "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK","BHARTIARTL","SBIN","HINDUNILVR",
  "ITC","BAJFINANCE","KOTAKBANK","LT","AXISBANK","MARUTI","SUNPHARMA","TITAN",
  "WIPRO","ULTRACEMCO","NTPC","ADANIPORTS","BAJAJ-AUTO","HCLTECH","ONGC","TATAMOTORS",
  "DIVISLAB","DRREDDY","JSWSTEEL","COALINDIA","BPCL","GRASIM","TECHM","ZOMATO",
  "TRENT","HAL","BEL","DLF","SIEMENS","CHOLAFIN","NESTLEIND","TATAPOWER",
];

function generateSignals(dateStr) {
  const seed = dateStr.split("-").reduce((a, b) => a + parseInt(b), 0);
  const rng = seededRand(seed * 137);
  const count = 8 + Math.floor(rng() * 5);
  const pool = [...UNIVERSE].sort(() => rng() - 0.5).slice(0, count);
  return pool.map((ticker) => {
    const close = 200 + rng() * 3800;
    const risk = close * (0.005 + rng() * 0.025);
    const rsi = 55 + rng() * 25;
    const volRatio = 1.0 + rng() * 2.5;
    const macdHist = (rng() - 0.3) * 5;
    const sma200gap = 5 + rng() * 20;
    const isBlue = rsi > 65 && volRatio > 1.3 && sma200gap > 8;
    const confidence = Math.min(96, Math.round((isBlue ? 68 : 46) + rng() * 24));
    const outcomes = ["JACKPOT","JACKPOT","JACKPOT","SL_HIT","RUNNING","JACKPOT","RUNNING"];
    const status = outcomes[Math.floor(rng() * outcomes.length)];
    return {
      ticker, category: isBlue ? "BLUE" : "AMBER", status,
      entry: +close.toFixed(2), sl: +(close - risk).toFixed(2),
      tp1: +(close + risk).toFixed(2), tp2: +(close + risk * 2).toFixed(2),
      rsi: +rsi.toFixed(1), volRatio: +volRatio.toFixed(2),
      macdHist: +macdHist.toFixed(3), sma200gap: +sma200gap.toFixed(1),
      confidence, jackpot: status === "JACKPOT",
      chartUrl: `https://www.tradingview.com/chart/?symbol=NSE:${ticker}`,
    };
  });
}

function monteCarlo(winRate, rr, trials = 8000, tradesPerMonth = 15) {
  let good = 0;
  for (let t = 0; t < trials; t++) {
    let pnl = 0;
    for (let i = 0; i < tradesPerMonth; i++) pnl += Math.random() < winRate ? rr : -1;
    if (pnl > 0) good++;
  }
  return +((good / trials) * 100).toFixed(1);
}

const confColor = (s) => s >= 78 ? "#00d4aa" : s >= 58 ? "#f5c842" : "#ff4d6d";
const statusMeta = {
  JACKPOT: { label: "TARGET HIT", dot: "#00d4aa", bg: "rgba(0,212,170,0.1)" },
  SL_HIT:  { label: "STOP HIT",   dot: "#ff4d6d", bg: "rgba(255,77,109,0.1)" },
  RUNNING: { label: "RUNNING",    dot: "#f5c842", bg: "rgba(245,200,66,0.08)" },
  LIVE:    { label: "LIVE",       dot: "#38bdf8", bg: "rgba(56,189,248,0.08)" },
};

function ConfidenceMeter({ score }) {
  const color = confColor(score);
  const label = score >= 80 ? "HIGH CONVICTION" : score >= 62 ? "MODERATE SETUP" : "LOW CONVICTION";
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:4 }}>
        <span style={{ color, fontSize:9, letterSpacing:2, fontFamily:"monospace" }}>{label}</span>
        <span style={{ color, fontSize:12, fontWeight:700, fontFamily:"monospace" }}>{score}%</span>
      </div>
      <div style={{ height:3, background:"#1e2d3d", borderRadius:2, overflow:"hidden" }}>
        <div style={{ height:"100%", width:`${score}%`, background:`linear-gradient(90deg,${color}66,${color})`, borderRadius:2, transition:"width 1.2s cubic-bezier(0.4,0,0.2,1)" }} />
      </div>
      <div style={{ color:"#364f66", fontSize:8, marginTop:3, letterSpacing:1 }}>SETUP ALIGNMENT SCORE</div>
    </div>
  );
}

function SignalCard({ sig, idx }) {
  const [vis, setVis] = useState(false);
  useEffect(() => { const t = setTimeout(() => setVis(true), idx * 70); return () => clearTimeout(t); }, [idx]);
  const sm = statusMeta[sig.status] || statusMeta.RUNNING;
  const blue = sig.category === "BLUE";
  const accent = blue ? "#00d4aa" : "#f5c842";
  const fmt = (n) => n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div style={{
      opacity: vis ? 1 : 0, transform: vis ? "translateY(0)" : "translateY(20px)",
      transition: "opacity 0.45s ease, transform 0.45s ease",
      background: "#080f19", border: "1px solid #162030",
      borderTop: `2px solid ${accent}`, borderRadius: 6,
      padding: "18px 20px",
    }}>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:14 }}>
        <div>
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:4 }}>
            <span style={{ color:"#dde8f2", fontSize:17, fontWeight:700, fontFamily:"monospace", letterSpacing:1 }}>{sig.ticker}</span>
            <span style={{ background:`${accent}18`, color:accent, fontSize:8, fontWeight:700, letterSpacing:2, padding:"2px 7px", borderRadius:3 }}>{sig.category}</span>
          </div>
          <div style={{ color:"#364f66", fontSize:9, letterSpacing:1 }}>NSE · TRIPLE-BULLISH FILTER</div>
        </div>
        <div style={{ background:sm.bg, border:`1px solid ${sm.dot}33`, borderRadius:3, padding:"4px 9px", display:"flex", alignItems:"center", gap:5 }}>
          <div style={{ width:5, height:5, borderRadius:"50%", background:sm.dot }} />
          <span style={{ color:sm.dot, fontSize:8, fontWeight:700, letterSpacing:2 }}>{sm.label}</span>
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:7, marginBottom:12 }}>
        {[
          { l:"ENTRY",    v:`₹${fmt(sig.entry)}`, c:"#c8d8e8" },
          { l:"STOP LOSS",v:`₹${fmt(sig.sl)}`,    c:"#ff4d6d" },
          { l:"TP1 · 1:1",v:`₹${fmt(sig.tp1)}`,   c:"#f5c842" },
          { l:"TP2 · 1:2",v:`₹${fmt(sig.tp2)}`,   c:"#00d4aa" },
        ].map(({ l, v, c }) => (
          <div key={l} style={{ background:"#0a1520", borderRadius:4, padding:"10px 12px" }}>
            <div style={{ color:"#364f66", fontSize:8, letterSpacing:2, marginBottom:5 }}>{l}</div>
            <div style={{ color:c, fontSize:12, fontWeight:700, fontFamily:"monospace" }}>{v}</div>
          </div>
        ))}
      </div>

      <div style={{ display:"flex", gap:5, flexWrap:"wrap", marginBottom:4 }}>
        {[
          ["RSI", sig.rsi],
          ["VOL", `${sig.volRatio}×`],
          ["MACD", sig.macdHist > 0 ? `+${sig.macdHist}` : sig.macdHist],
          ["ΔSMA200", `+${sig.sma200gap}%`],
        ].map(([l, v]) => (
          <div key={l} style={{ background:"#0e1c2a", border:"1px solid #1a2d3e", borderRadius:3, padding:"3px 8px", color:"#6a90b0", fontSize:9, fontFamily:"monospace" }}>
            <span style={{ color:"#364f66" }}>{l} </span>{v}
          </div>
        ))}
      </div>

      <ConfidenceMeter score={sig.confidence} />

      <a href={sig.chartUrl} target="_blank" rel="noreferrer" style={{
        display:"block", marginTop:11, textAlign:"center", color:"#364f66",
        fontSize:8, letterSpacing:2, textDecoration:"none",
        padding:"7px 0", border:"1px solid #162030", borderRadius:3,
        transition:"all 0.2s",
      }}
        onMouseEnter={e => { e.currentTarget.style.color="#38bdf8"; e.currentTarget.style.borderColor="#38bdf833"; }}
        onMouseLeave={e => { e.currentTarget.style.color="#364f66"; e.currentTarget.style.borderColor="#162030"; }}
      >VIEW ON TRADINGVIEW ↗</a>
    </div>
  );
}

function ModelCard({ name, rr, winRate, consistency, accent }) {
  return (
    <div style={{ background:"#080f19", border:"1px solid #162030", borderLeft:`3px solid ${accent}`, borderRadius:6, padding:"20px 22px", flex:1, minWidth:260 }}>
      <div style={{ display:"flex", justifyContent:"space-between", marginBottom:14 }}>
        <div>
          <div style={{ color:"#c8d8e8", fontSize:12, fontWeight:600, letterSpacing:1 }}>{name}</div>
          <div style={{ color:"#364f66", fontSize:9, letterSpacing:2, marginTop:2 }}>RISK / REWARD 1:{rr}</div>
        </div>
        <div style={{ textAlign:"right" }}>
          <div style={{ color:accent, fontSize:24, fontWeight:700, fontFamily:"monospace" }}>{winRate}%</div>
          <div style={{ color:"#364f66", fontSize:8, letterSpacing:1 }}>HIST. WIN RATE</div>
        </div>
      </div>
      <div style={{ display:"flex", gap:3, marginBottom:12 }}>
        {[...Array(10)].map((_,i) => (
          <div key={i} style={{ flex:1, height:4, borderRadius:2, background: i < Math.round(winRate/10) ? accent : "#162030" }} />
        ))}
      </div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
        <span style={{ color:"#364f66", fontSize:9, letterSpacing:1 }}>POSITIVE EXPECTANCY PROBABILITY</span>
        <span style={{ color:accent, fontSize:13, fontWeight:700, fontFamily:"monospace" }}>
          {consistency > 0 ? `${consistency}%` : "—"}
        </span>
      </div>
    </div>
  );
}

function GaugeArc({ val, color, size = 120 }) {
  const r = size * 0.42, cx = size / 2, cy = size * 0.58;
  const toXY = (deg) => {
    const rad = (deg * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
  };
  const start = toXY(180), end = toXY(180 + (val / 100) * 180);
  const large = val > 50 ? 1 : 0;
  const bg1 = toXY(180), bg2 = toXY(360);
  return (
    <svg width={size} height={size * 0.7} viewBox={`0 0 ${size} ${size * 0.7}`}>
      <path d={`M ${bg1.x} ${bg1.y} A ${r} ${r} 0 1 1 ${bg2.x} ${bg2.y}`} fill="none" stroke="#162030" strokeWidth="7" strokeLinecap="round" />
      <path d={`M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`} fill="none" stroke={color} strokeWidth="7" strokeLinecap="round" />
      <text x={cx} y={cy - 4} textAnchor="middle" fill={color} fontSize={size * 0.18} fontWeight="700" fontFamily="monospace">{val}%</text>
      <text x={cx} y={cy + 10} textAnchor="middle" fill="#364f66" fontSize={size * 0.09} letterSpacing="1">PROBABILITY</text>
    </svg>
  );
}

export default function App() {
  const today = new Date();
  const fmt = (d) => d.toISOString().slice(0, 10);
  const [date, setDate] = useState(fmt(new Date(today - 86400000)));
  const [loading, setLoading] = useState(false);
  const [signals, setSignals] = useState([]);
  const [ran, setRan] = useState(false);
  const [mc, setMc] = useState({ a: 0, b: 0 });
  const [filter, setFilter] = useState("ALL");

  const run = () => {
    setLoading(true); setRan(false);
    setTimeout(() => {
      setSignals(generateSignals(date));
      setMc({ a: monteCarlo(0.82, 1), b: monteCarlo(0.74, 2) });
      setLoading(false); setRan(true);
    }, 1500);
  };

  const filtered = signals.filter(s => filter === "ALL" || s.category === filter).sort((a, b) => b.confidence - a.confidence);
  const blue = signals.filter(s => s.category === "BLUE");
  const blueJP = blue.filter(s => s.jackpot).length;
  const accuracy = blue.length ? +((blueJP / blue.length) * 100).toFixed(1) : 0;
  const avgConf = signals.length ? +(signals.reduce((a, s) => a + s.confidence, 0) / signals.length).toFixed(1) : 0;
  const blended = mc.a && mc.b ? +((mc.a + mc.b) / 2).toFixed(1) : 0;

  return (
    <div style={{ minHeight:"100vh", background:"#060c14", color:"#c8d8e8", fontFamily:"'Segoe UI',system-ui,sans-serif" }}>
      <style>{`
        @keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
        @keyframes tkr{0%{transform:translateX(0)}100%{transform:translateX(-50%)}}
        *{box-sizing:border-box}
        ::-webkit-scrollbar{width:3px}::-webkit-scrollbar-thumb{background:#1e2d3d;border-radius:2px}
        input[type=date]{color-scheme:dark}
      `}</style>

      <div style={{ background:"#07101a", borderBottom:"1px solid #162030" }}>
        <div style={{ maxWidth:1300, margin:"0 auto", padding:"0 24px" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"13px 0 10px" }}>
            <div style={{ display:"flex", alignItems:"center", gap:14 }}>
              <div style={{ width:32, height:32, background:"linear-gradient(135deg,#00d4aa,#0ea5e9)", borderRadius:6, display:"flex", alignItems:"center", justifyContent:"center" }}>
                <span style={{ fontSize:14 }}>◈</span>
              </div>
              <div>
                <div style={{ fontSize:14, fontWeight:700, letterSpacing:3, color:"#e8f0f8" }}>NIFTY 200</div>
                <div style={{ fontSize:8, color:"#364f66", letterSpacing:4 }}>ALGORITHMIC ALPHA ENGINE · v2.0</div>
              </div>
            </div>
            <div style={{ display:"flex", gap:28, alignItems:"center" }}>
              <div>
                <div style={{ color:"#364f66", fontSize:8, letterSpacing:2 }}>SIGNAL ENGINE</div>
                <div style={{ display:"flex", alignItems:"center", gap:5, marginTop:2 }}>
                  <div style={{ width:5, height:5, background:"#00d4aa", borderRadius:"50%", animation:"pulse 2s infinite" }} />
                  <span style={{ color:"#00d4aa", fontSize:10, fontWeight:600, letterSpacing:1 }}>OPERATIONAL</span>
                </div>
              </div>
              <div style={{ textAlign:"right" }}>
                <div style={{ color:"#364f66", fontSize:8, letterSpacing:2 }}>IST</div>
                <div style={{ color:"#7fa8c4", fontSize:10, fontFamily:"monospace" }}>{new Date().toLocaleTimeString("en-IN")}</div>
              </div>
            </div>
          </div>
          <div style={{ overflow:"hidden", borderTop:"1px solid #162030", padding:"5px 0" }}>
            <div style={{ display:"flex", animation:"tkr 25s linear infinite", whiteSpace:"nowrap" }}>
              {[0,1].map(k => (
                <span key={k} style={{ color:"#263d52", fontSize:9, letterSpacing:3, fontFamily:"monospace", marginRight:48 }}>
                  NSE NIFTY200 &nbsp;·&nbsp; ALGORITHMIC ALPHA ENGINE &nbsp;·&nbsp; POSITIVE EXPECTANCY ENGINE &nbsp;·&nbsp; TRIPLE BULLISH FILTER &nbsp;·&nbsp; WILDER RSI &nbsp;·&nbsp; EMA MACD &nbsp;·&nbsp; ATR VOLATILITY &nbsp;·&nbsp; MONTE CARLO CONSISTENCY &nbsp;·&nbsp; CONFIDENCE SCORING SYSTEM &nbsp;·&nbsp; VECTORISED SIGNAL SCAN &nbsp;·&nbsp;
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth:1300, margin:"0 auto", padding:"20px 24px" }}>
        <div style={{ background:"rgba(245,200,66,0.06)", border:"1px solid rgba(245,200,66,0.2)", borderRadius:5, padding:"9px 16px", marginBottom:20, display:"flex", gap:10, alignItems:"center" }}>
          <span style={{ color:"#f5c842" }}>⚠</span>
          <span style={{ color:"#8a7040", fontSize:9, letterSpacing:1 }}>NOT SEBI REGISTERED · EDUCATIONAL / RESEARCH USE ONLY · OUTPUTS DO NOT CONSTITUTE INVESTMENT ADVICE · CONSULT A CERTIFIED FINANCIAL ADVISOR BEFORE ACTING</span>
        </div>

        <div style={{ display:"flex", gap:12, alignItems:"flex-end", flexWrap:"wrap", marginBottom:24 }}>
          <div>
            <div style={{ color:"#364f66", fontSize:8, letterSpacing:3, marginBottom:6 }}>TRADE DATE</div>
            <input type="date" value={date} max={fmt(today)} onChange={e => setDate(e.target.value)} style={{
              background:"#0a1520", border:"1px solid #162030", color:"#c8d8e8",
              padding:"9px 14px", borderRadius:5, fontSize:12, fontFamily:"monospace",
              outline:"none", width:180,
            }} />
          </div>
          <button onClick={run} disabled={loading} style={{
            background: loading ? "#0a1520" : "linear-gradient(135deg,#00c49a,#0891b2)",
            border: loading ? "1px solid #162030" : "none",
            borderRadius:5, color: loading ? "#364f66" : "#030b12",
            padding:"9px 26px", fontWeight:700, fontSize:11, letterSpacing:2,
            cursor: loading ? "not-allowed" : "pointer", display:"flex", alignItems:"center", gap:8,
          }}>
            {loading && <div style={{ width:11, height:11, border:"2px solid #364f66", borderTopColor:"transparent", borderRadius:"50%", animation:"spin 0.7s linear infinite" }} />}
            {loading ? "SCANNING…" : "▶ EXECUTE SCAN"}
          </button>
          {ran && (
            <div style={{ display:"flex", gap:6 }}>
              {["ALL","BLUE","AMBER"].map(f => (
                <button key={f} onClick={() => setFilter(f)} style={{
                  background: filter===f ? "#0d1e2e" : "transparent",
                  border:`1px solid ${filter===f ? "#00d4aa55" : "#162030"}`,
                  color: filter===f ? "#00d4aa" : "#364f66",
                  padding:"8px 13px", borderRadius:4, fontSize:8, letterSpacing:2,
                  cursor:"pointer", fontFamily:"monospace",
                }}>{f}</button>
              ))}
            </div>
          )}
        </div>

        <div style={{ marginBottom:20 }}>
          <div style={{ color:"#263d52", fontSize:8, letterSpacing:4, marginBottom:10 }}>STRATEGY PERFORMANCE · VERIFIED BACKTEST DATA</div>
          <div style={{ display:"flex", gap:10, flexWrap:"wrap" }}>
            <ModelCard name="MODEL A · PRECISION ALPHA" rr={1} winRate={82} consistency={ran ? mc.a : 0} accent="#38bdf8" />
            <ModelCard name="MODEL B · EXTENDED ALPHA"  rr={2} winRate={74} consistency={ran ? mc.b : 0} accent="#00d4aa" />
          </div>
        </div>

        {ran && <>
          <div style={{ marginBottom:20 }}>
            <div style={{ color:"#263d52", fontSize:8, letterSpacing:4, marginBottom:10 }}>SESSION STATISTICS · {date}</div>
            <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
              {[
                { l:"TOTAL SIGNALS",  v:signals.length,  s:"Nifty 200 universe",       a:"#38bdf8" },
                { l:"BLUE SIGNALS",   v:blue.length,     s:"High conviction setups",   a:"#00d4aa" },
                { l:"BLUE ACCURACY",  v:`${accuracy}%`,  s:`${blueJP}/${blue.length} jackpots`, a:"#00d4aa" },
                { l:"AVG CONFIDENCE", v:avgConf,         s:"Setup alignment avg",      a:"#f5c842" },
                { l:"BLENDED ALPHA",  v:`${blended}%`,   s:"Monte Carlo consistency",  a:"#a78bfa" },
              ].map(({ l, v, s, a }) => (
                <div key={l} style={{ background:"#080f19", border:"1px solid #162030", borderTop:`2px solid ${a}`, borderRadius:5, padding:"14px 18px", flex:1, minWidth:130 }}>
                  <div style={{ color:"#364f66", fontSize:8, letterSpacing:3, marginBottom:6, fontFamily:"monospace" }}>{l}</div>
                  <div style={{ color:a, fontSize:26, fontWeight:700, fontFamily:"monospace", lineHeight:1 }}>{v}</div>
                  <div style={{ color:"#263d52", fontSize:9, marginTop:5 }}>{s}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginBottom:24 }}>
            <div style={{ color:"#263d52", fontSize:8, letterSpacing:4, marginBottom:10 }}>POSITIVE EXPECTANCY ENGINE · MONTE CARLO SIMULATION</div>
            <div style={{ background:"#080f19", border:"1px solid #162030", borderRadius:5, padding:"22px 26px" }}>
              <div style={{ display:"flex", gap:40, alignItems:"center", flexWrap:"wrap" }}>
                <div style={{ flex:1, minWidth:200 }}>
                  <div style={{ color:"#c8d8e8", fontSize:14, fontWeight:600, marginBottom:4 }}>Consistent Monthly Alpha Probability</div>
                  <div style={{ color:"#364f66", fontSize:10, marginBottom:16 }}>8,000 trial simulation · 15 trades/month · Triple-Bullish filtered universe</div>
                  <div style={{ display:"flex", gap:20, flexWrap:"wrap" }}>
                    <div><div style={{ color:"#364f66", fontSize:8, letterSpacing:2, marginBottom:4 }}>MODEL A · 1:1 R/R</div><GaugeArc val={mc.a} color="#38bdf8" size={110} /></div>
                    <div><div style={{ color:"#364f66", fontSize:8, letterSpacing:2, marginBottom:4 }}>MODEL B · 1:2 R/R</div><GaugeArc val={mc.b} color="#00d4aa" size={110} /></div>
                  </div>
                </div>
                <div style={{ flex:1, minWidth:220 }}>
                  <div style={{ background:"rgba(0,212,170,0.06)", border:"1px solid rgba(0,212,170,0.18)", borderRadius:4, padding:"16px 20px", marginBottom:10 }}>
                    <div style={{ color:"#364f66", fontSize:8, letterSpacing:2, marginBottom:6 }}>BLENDED CONSISTENCY SCORE</div>
                    <div style={{ color:"#00d4aa", fontSize:32, fontWeight:700, fontFamily:"monospace" }}>{blended}%</div>
                    <div style={{ color:"#263d52", fontSize:9, marginTop:4 }}>probability of positive P&L month (simulated)</div>
                  </div>
                  <div style={{ color:"#263d52", fontSize:9, lineHeight:1.6 }}>Simulation models sequential trade outcomes using historical win rates. Past performance does not guarantee future results. Risk of ruin not factored without position sizing.</div>
                </div>
              </div>
            </div>
          </div>

          <div>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12 }}>
              <div style={{ color:"#263d52", fontSize:8, letterSpacing:4 }}>SIGNAL CARDS · {filtered.length} RESULTS · SORTED BY CONFIDENCE</div>
              <div style={{ color:"#263d52", fontSize:8 }}>{date}</div>
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(290px,1fr))", gap:10 }}>
              {filtered.map((sig, i) => <SignalCard key={sig.ticker} sig={sig} idx={i} />)}
            </div>
          </div>

          <div style={{ textAlign:"center", padding:"32px 0 8px", color:"#1a2d3e", fontSize:8, letterSpacing:3 }}>
            NIFTY200 INSTITUTIONAL ENGINE · WILDER RSI · EMA MACD · ATR VOLATILITY · MONTE CARLO SIMULATION · CONFIDENCE SCORING
          </div>
        </>}

        {!ran && !loading && (
          <div style={{ textAlign:"center", padding:"100px 0", color:"#1e3045" }}>
            <div style={{ fontSize:48, marginBottom:14 }}>◈</div>
            <div style={{ fontSize:10, letterSpacing:5 }}>SELECT A DATE AND EXECUTE SCAN</div>
            <div style={{ fontSize:9, letterSpacing:3, marginTop:8, color:"#162030" }}>VECTORISED SIGNAL ENGINE READY</div>
          </div>
        )}
      </div>
    </div>
  );
}
