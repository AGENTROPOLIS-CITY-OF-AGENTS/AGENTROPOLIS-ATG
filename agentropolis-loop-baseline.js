(() => {
  if (window.__AGENTROPOLIS_LOOP_BASELINE__) return;
  window.__AGENTROPOLIS_LOOP_BASELINE__ = true;
  window.__AGENTROPOLIS_LOOP_BASELINE_VERSION__ = '1.0.0';

  const host = document.createElement('div');
  host.id = 'agentropolis-loop-baseline';
  host.style.position = 'fixed';
  host.style.zIndex = '2147483000';
  host.style.right = '14px';
  host.style.bottom = '14px';
  document.body.appendChild(host);

  const root = host.attachShadow({mode: 'open'});
  root.innerHTML = `
    <style>
      :host{all:initial}
      *{box-sizing:border-box}
      .wrap{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#f4f7fb}
      button{font:inherit}
      .trigger{border:1px solid #19e6e6;background:#05070a;color:#19e6e6;border-radius:999px;padding:9px 12px;font-weight:800;font-size:11px;letter-spacing:.08em;box-shadow:0 8px 28px rgba(0,0,0,.4);cursor:pointer}
      .panel{width:min(420px,calc(100vw - 28px));margin-bottom:9px;border:1px solid #1d2a33;background:rgba(5,7,10,.97);border-radius:16px;padding:15px;box-shadow:0 18px 70px rgba(0,0,0,.55)}
      .panel[hidden]{display:none}
      .k{font:800 10px/1.2 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.16em;color:#19e6e6}
      h2{margin:7px 0 6px;font-size:17px;line-height:1.15}
      p{margin:7px 0;color:#aeb8c4;font-size:12px;line-height:1.5}
      .flow{display:grid;gap:5px;margin:11px 0}
      .node{border:1px solid #1d2a33;border-radius:9px;padding:7px 9px;background:#0b0f14;font-size:11px}
      .cyan{border-color:rgba(25,230,230,.45)}
      .red{border-color:rgba(255,42,42,.45)}
      .row{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}
      .row .node{text-align:center}
      .rule{border-left:3px solid #ff2a2a;padding-left:9px;color:#f4f7fb}
      .chips{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}
      .chip{border:1px solid #1d2a33;border-radius:999px;padding:4px 7px;color:#aeb8c4;font-size:10px}
      a{color:#19e6e6;text-decoration:none;font-size:11px}
      .footer{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-top:10px}
      @media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
    </style>
    <div class="wrap">
      <section class="panel" id="agt-loop-panel" hidden aria-label="AGENTROPOLIS bounded cognition baseline">
        <div class="k">AGENTROPOLIS // BOUNDED COGNITION</div>
        <h2>Loop Engineering Baseline</h2>
        <p>Every autonomous loop begins bounded, measured and verifiable.</p>
        <div class="flow">
          <div class="node">CHEAP GATES · exact checks before model spend</div>
          <div class="node">REFLEX DECISION · typed route + confidence</div>
          <div class="node cyan">QRAG · Retrieve → Evaluate → Execute → Verify → Re-query</div>
          <div class="node">DENSE FEEDBACK · attributable measurements</div>
          <div class="row">
            <div class="node cyan">INCREASE</div>
            <div class="node red">DECREASE</div>
            <div class="node cyan">REDIRECT</div>
          </div>
          <div class="node">QUANTIZATION TORQUE · allocate minimum sufficient intelligence</div>
          <div class="node">VERITY → RECEIPT → AUDIT</div>
        </div>
        <p class="rule"><b>Classifier output is evidence, not authority.</b> Policy and the Execution Envelope remain authoritative.</p>
        <div class="chips"><span class="chip">TOKEN BUDGET</span><span class="chip">COST BUDGET</span><span class="chip">QUALITY FLOOR</span><span class="chip">RETRY LIMIT</span></div>
        <div class="footer">
          <span class="k">PRESERVE WHAT MATTERS.</span>
          <a href="https://agentropolis-city-of-agents.github.io/AGENTROPOLIS-DESIGN-SYSTEM/" target="_blank" rel="noreferrer">Design system ↗</a>
        </div>
      </section>
      <button class="trigger" id="agt-loop-trigger" type="button" aria-expanded="false" aria-controls="agt-loop-panel">QRAG BASELINE</button>
    </div>`;

  const btn = root.getElementById('agt-loop-trigger');
  const panel = root.getElementById('agt-loop-panel');
  btn.addEventListener('click', () => {
    const open = panel.hasAttribute('hidden');
    if (open) panel.removeAttribute('hidden'); else panel.setAttribute('hidden','');
    btn.setAttribute('aria-expanded', String(open));
  });
})();