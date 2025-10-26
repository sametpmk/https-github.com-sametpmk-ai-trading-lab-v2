# app/dashboard.py
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text
from datetime import datetime
import json

router = APIRouter()

def _dictify(row):
    return {k: row._mapping[k] for k in row._mapping.keys()}

@router.get("/api/summary")
def api_summary():
    # trades tablosundan metrikler
    from .storage import Storage
    db = Storage("data/results.sqlite")  # aynı path
    with db.engine.begin() as conn:
        # Toplam PnL, trade sayısı, win%
        totals = conn.execute(text("""
            SELECT COUNT(*) AS n_trades,
                   SUM(CASE WHEN pnl>0 THEN 1 ELSE 0 END) AS wins,
                   SUM(pnl) AS total_pnl
            FROM trades
        """)).first()

        # En iyi 5 strateji
        top_strats = conn.execute(text("""
            SELECT strategy_id, ROUND(SUM(pnl), 4) AS pnl, COUNT(*) AS n
            FROM trades
            GROUP BY strategy_id
            ORDER BY pnl DESC
            LIMIT 5
        """)).fetchall()

        # En iyi 5 sembol
        top_syms = conn.execute(text("""
            SELECT symbol, ROUND(SUM(pnl), 4) AS pnl, COUNT(*) AS n
            FROM trades
            GROUP BY symbol
            ORDER BY pnl DESC
            LIMIT 5
        """)).fetchall()

    n_trades = totals[0] or 0
    wins = totals[1] or 0
    total_pnl = float(totals[2] or 0.0)
    winrate = (wins / n_trades * 100) if n_trades > 0 else 0.0

    return JSONResponse({
        "n_trades": n_trades,
        "wins": wins,
        "winrate": round(winrate, 2),
        "total_pnl": round(total_pnl, 4),
        "top_strategies": [dict(strategy_id=r[0], pnl=float(r[1] or 0.0), n=r[2]) for r in top_strats],
        "top_symbols": [dict(symbol=r[0], pnl=float(r[1] or 0.0), n=r[2]) for r in top_syms],
    })


@router.get("/api/equity")
def api_equity():
    # Kapaniş zamanına göre kümülatif PnL eğrisi
    from .storage import Storage
    db = Storage("data/results.sqlite")
    with db.engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT ts_close, pnl
            FROM trades
            ORDER BY ts_close ASC
        """)).fetchall()

    equity = []
    cum = 0.0
    for r in rows:
        ts = r[0] if isinstance(r[0], datetime) else datetime.fromisoformat(str(r[0]))
        cum += float(r[1] or 0.0)
        equity.append({"t": ts.isoformat().replace("+00:00",""), "v": round(cum, 6)})

    return JSONResponse({"equity": equity})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    # Basit HTML + Chart.js (CDN). Veriyi /api/* uçlarından çeker.
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>AI Trading Lab – Dashboard</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:24px;color:#111;background:#0b0f14}
    h1,h2,h3{color:#e6edf3}
    .grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}
    .card{grid-column:span 12;background:#0f1720;border:1px solid #1f2937;border-radius:14px;padding:16px}
    @media(min-width:900px){
      .col-4{grid-column:span 4}
      .col-8{grid-column:span 8}
      .col-6{grid-column:span 6}
    }
    .kpi{display:flex;gap:16px;flex-wrap:wrap}
    .k{background:#111827;border:1px solid #1f2937;border-radius:12px;padding:12px 16px;min-width:160px}
    .label{color:#9ca3af;font-size:12px;text-transform:uppercase;letter-spacing:.06em}
    .val{color:#e5e7eb;font-size:22px;font-weight:700;margin-top:4px}
    table{width:100%;border-collapse:collapse;color:#e5e7eb}
    th,td{padding:8px;border-bottom:1px solid #1f2937;text-align:left}
    th{color:#9ca3af;font-weight:600;font-size:12px;text-transform:uppercase}
    canvas{max-height:360px}
    a{color:#60a5fa}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
  <h1>AI Trading Lab – Dashboard</h1>
  <div class="grid">
    <div class="card col-12">
      <div class="kpi" id="kpis">
        <div class="k"><div class="label">Toplam PnL</div><div class="val" id="k-totalpnl">—</div></div>
        <div class="k"><div class="label">İşlem Sayısı</div><div class="val" id="k-trades">—</div></div>
        <div class="k"><div class="label">Win %</div><div class="val" id="k-winrate">—</div></div>
      </div>
    </div>

    <div class="card col-8">
      <h3>Eküiti Eğrisi</h3>
      <canvas id="equityChart"></canvas>
    </div>
    <div class="card col-4">
      <h3>En İyi 5 Strateji</h3>
      <table id="tblStrats"><thead><tr><th>Strateji</th><th>PnL</th><th>İşlem</th></tr></thead><tbody></tbody></table>
      <h3>En İyi 5 Sembol</h3>
      <table id="tblSyms"><thead><tr><th>Sembol</th><th>PnL</th><th>İşlem</th></tr></thead><tbody></tbody></table>
    </div>

    <div class="card col-12">
      <small>API: <a href="/status">/status</a> · <a href="/api/summary">/api/summary</a> · <a href="/api/equity">/api/equity</a></small>
    </div>
  </div>

<script>
async function loadSummary(){
  const r = await fetch('/api/summary'); const j = await r.json();
  document.getElementById('k-totalpnl').textContent = j.total_pnl.toFixed(4);
  document.getElementById('k-trades').textContent = j.n_trades;
  document.getElementById('k-winrate').textContent = j.winrate.toFixed(2)+'%';

  const tbS = document.querySelector('#tblStrats tbody'); tbS.innerHTML='';
  j.top_strategies.forEach(x=>{
    const tr=document.createElement('tr');
    tr.innerHTML = `<td>${x.strategy_id}</td><td>${x.pnl.toFixed(4)}</td><td>${x.n}</td>`;
    tbS.appendChild(tr);
  });

  const tbY = document.querySelector('#tblSyms tbody'); tbY.innerHTML='';
  j.top_symbols.forEach(x=>{
    const tr=document.createElement('tr');
    tr.innerHTML = `<td>${x.symbol}</td><td>${x.pnl.toFixed(4)}</td><td>${x.n}</td>`;
    tbY.appendChild(tr);
  });
}

async function loadEquity(){
  const r = await fetch('/api/equity'); const j = await r.json();
  const ctx = document.getElementById('equityChart').getContext('2d');
  const labels = j.equity.map(p=>p.t);
  const data = j.equity.map(p=>p.v);
  new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: [{ label: 'Equity', data, fill: false, tension: 0.2 }] },
    options: {
      responsive: true,
      scales: { x: { ticks: { color:'#9ca3af' } }, y: { ticks: { color:'#9ca3af' } } },
      plugins: { legend: { labels: { color:'#e5e7eb' } } }
    }
  });
}

loadSummary(); loadEquity();
setInterval(loadSummary, 15000);
</script>
</body>
</html>
    """
    return HTMLResponse(html)
