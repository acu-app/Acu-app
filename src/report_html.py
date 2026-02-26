import os
import json
from datetime import datetime


def _pct(x: float) -> str:
    return f"{x*100:.0f}%"


def _fmt_vol(x: float) -> str:
    return f"{x:.1f}%"


def generate_html_report(analysis_json_path: str) -> str:
    """
    Lee output/.../analysis.json y genera report.html en la misma carpeta.
    """
    if not os.path.exists(analysis_json_path):
        raise FileNotFoundError(f"No existe: {analysis_json_path}")

    out_dir = os.path.dirname(analysis_json_path)

    with open(analysis_json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    analysis = payload.get("analysis", {})
    metrics = analysis.get("metrics", {})
    alerts = analysis.get("alerts", [])
    recs = analysis.get("recommendations", [])
    top_holdings = analysis.get("top_holdings", [])
    scenarios = analysis.get("scenarios", [])
    perfil = analysis.get("perfil_declarado", "Moderada")

    vol = metrics.get("VolPromedioCartera", 0.0)
    score = metrics.get("ScorePromedioCartera", 0.0)
    top1 = metrics.get("ConcentracionTop1", 0.0)
    top3 = metrics.get("ConcentracionTop3", 0.0)
    hhi = metrics.get("IndiceHerfindahl", 0.0)

    exp_pais = metrics.get("ExposicionPorPais", {})
    exp_tipo = metrics.get("ExposicionPorTipo", {})

    def render_table_kv(title, d):
        rows = "".join([f"<tr><td>{k}</td><td>{_pct(v)}</td></tr>" for k, v in list(d.items())[:10]])
        return f"""
        <div class="card">
          <h3>{title}</h3>
          <table>
            <thead><tr><th>Categoria</th><th>Peso</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """

    alerts_html = "".join([f"<li>{a.get('msg')}</li>" for a in alerts]) or "<li>Sin alertas críticas.</li>"
    recs_html = "".join([f"<li><b>{r.get('title')}</b>: {r.get('detail')}</li>" for r in recs]) or "<li>Sin recomendaciones automáticas.</li>"

    top_html_rows = "".join([
        f"<tr><td>{a.get('Activo')}</td><td>{a.get('Tipo')}</td><td>{a.get('Pais')}</td><td>{_pct(float(a.get('Peso',0)))}</td><td>{_fmt_vol(float(a.get('VolatilidadFinal',0)))}</td></tr>"
        for a in top_holdings
    ])

    scenarios_rows = "".join([
        f"<tr><td>{s.get('label')}</td><td>{_fmt_vol(s.get('metrics_after',{}).get('VolPromedioCartera',0))}</td>"
        f"<td>{s.get('metrics_after',{}).get('ConcentracionTop3',0):.2f}</td><td>{s.get('metrics_after',{}).get('IndiceHerfindahl',0):.2f}</td></tr>"
        for s in scenarios
    ]) or "<tr><td colspan='4'>Sin escenarios.</td></tr>"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>Reporte de Cartera</title>
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial; margin: 24px; color: #111; }}
        .header {{ display:flex; justify-content:space-between; align-items:flex-end; border-bottom:1px solid #ddd; padding-bottom:12px; }}
        .grid {{ display:grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px; }}
        .card {{ border:1px solid #e5e5e5; border-radius:12px; padding:14px; }}
        .kpi {{ font-size: 26px; font-weight: 700; }}
        .label {{ color:#666; font-size: 12px; }}
        h2 {{ margin-top: 26px; }}
        table {{ width:100%; border-collapse: collapse; }}
        th, td {{ border-bottom: 1px solid #eee; padding: 8px; text-align:left; font-size: 13px; }}
        ul {{ margin: 8px 0 0 18px; }}
      </style>
    </head>
    <body>
      <div class="header">
        <div>
          <div class="label">Reporte de Cartera</div>
          <h1 style="margin:6px 0 0 0;">Diagnóstico + Recomendaciones</h1>
          <div class="label">Perfil considerado: <b>{perfil}</b></div>
        </div>
        <div class="label">Generado: {now}</div>
      </div>

      <div class="grid">
        <div class="card"><div class="label">Volatilidad promedio</div><div class="kpi">{_fmt_vol(vol)}</div></div>
        <div class="card"><div class="label">Score promedio</div><div class="kpi">{score:.1f}</div></div>
        <div class="card"><div class="label">Concentración Top 3</div><div class="kpi">{_pct(top3)}</div></div>
        <div class="card"><div class="label">Concentración Top 1</div><div class="kpi">{_pct(top1)}</div></div>
        <div class="card"><div class="label">Índice Herfindahl</div><div class="kpi">{hhi:.2f}</div></div>
      </div>

      <h2>Alertas</h2>
      <div class="card"><ul>{alerts_html}</ul></div>

      <h2>Recomendaciones</h2>
      <div class="card"><ul>{recs_html}</ul></div>

      <h2>Exposición</h2>
      <div class="grid">
        {render_table_kv("Exposición por País", exp_pais)}
        {render_table_kv("Exposición por Tipo", exp_tipo)}
      </div>

      <h2>Top holdings</h2>
      <div class="card">
        <table>
          <thead><tr><th>Activo</th><th>Tipo</th><th>País</th><th>Peso</th><th>Vol</th></tr></thead>
          <tbody>
            {top_html_rows}
          </tbody>
        </table>
      </div>

      <h2>Escenarios (sensibilidad)</h2>
      <div class="card">
        <table>
          <thead><tr><th>Escenario</th><th>Vol after</th><th>Top3 after</th><th>HHI after</th></tr></thead>
          <tbody>
            {scenarios_rows}
          </tbody>
        </table>
      </div>

      <div class="label" style="margin-top:22px;">
        Nota: Diagnóstico automático basado en reglas. No constituye recomendación de inversión.
      </div>
    </body>
    </html>
    """

    out_path = os.path.join(out_dir, "report.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ Reporte HTML generado:", out_path)
    return out_path
