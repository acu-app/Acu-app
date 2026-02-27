from __future__ import annotations
from datetime import datetime
from typing import Dict, Any


def generate_profile_html(profile_payload: Dict[str, Any]) -> str:
    """
    Recibe el payload que genera el cuestionario (tus respuestas + score + perfil_sugerido)
    y devuelve un HTML prolijo para compartir / imprimir a PDF.
    """
    meta = profile_payload.get("meta", {})
    answers = profile_payload.get("answers", {})
    result = profile_payload.get("result", {})

    client_name = meta.get("client_name", "Cliente")
    created_at = meta.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M")
    score = result.get("score_total", "")
    perfil = result.get("perfil_sugerido", "")
    rationale = result.get("rationale", [])

    def row(label: str, value: str) -> str:
        return f"""
        <div class="row">
          <div class="label">{label}</div>
          <div class="value">{value}</div>
        </div>
        """

    # Render respuestas
    answers_html = ""
    for k, v in answers.items():
        answers_html += row(k, str(v))

    # Render rationale bullets
    bullets = ""
    for b in rationale:
        bullets += f"<li>{b}</li>"

    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ACU • Perfil del Cliente</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      color: #111827;
      margin: 0;
      background: #f6f7fb;
    }}
    .page {{
      max-width: 900px;
      margin: 32px auto;
      padding: 24px;
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 16px;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      border-bottom: 1px solid #e5e7eb;
      padding-bottom: 16px;
      margin-bottom: 16px;
    }}
    .brand {{
      font-weight: 800;
      letter-spacing: 0.5px;
      font-size: 18px;
    }}
    .title {{
      font-size: 26px;
      font-weight: 800;
      margin: 6px 0 0;
    }}
    .muted {{ color: #6b7280; font-size: 13px; }}
    .pill {{
      display: inline-block;
      padding: 8px 12px;
      border-radius: 999px;
      background: #111827;
      color: #fff;
      font-weight: 700;
      font-size: 13px;
      white-space: nowrap;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 16px;
    }}
    .card {{
      border: 1px solid #e5e7eb;
      border-radius: 14px;
      padding: 16px;
      background: #fff;
    }}
    .card h3 {{
      margin: 0 0 10px;
      font-size: 14px;
      color: #111827;
      letter-spacing: 0.3px;
      text-transform: uppercase;
    }}
    .row {{
      display: grid;
      grid-template-columns: 1fr 1.2fr;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 1px dashed #e5e7eb;
    }}
    .row:last-child {{ border-bottom: none; }}
    .label {{ color: #374151; font-weight: 600; font-size: 13px; }}
    .value {{ color: #111827; font-size: 13px; }}
    ul {{ margin: 8px 0 0 18px; color: #111827; }}
    .footer {{
      margin-top: 16px;
      padding-top: 12px;
      border-top: 1px solid #e5e7eb;
      font-size: 12px;
      color: #6b7280;
    }}
    @media print {{
      body {{ background: #fff; }}
      .page {{ margin: 0; border: none; border-radius: 0; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <div class="header">
      <div>
        <div class="brand">ACU</div>
        <div class="title">Perfil del Cliente</div>
        <div class="muted">{client_name} • Generado: {created_at}</div>
      </div>
      <div style="text-align:right;">
        <div class="pill">Perfil sugerido: {perfil}</div>
        <div class="muted" style="margin-top:8px;">Score total: {score}</div>
      </div>
    </div>

    <div class="grid">
      <div class="card">
        <h3>Respuestas</h3>
        {answers_html}
      </div>

      <div class="card">
        <h3>Interpretación</h3>
        <div class="muted">Por qué se sugiere este perfil:</div>
        <ul>
          {bullets}
        </ul>
      </div>
    </div>

    <div class="footer">
      Este documento es informativo y no constituye recomendación de inversión. Elaborado a partir de respuestas declaradas por el cliente.
    </div>
  </div>
</body>
</html>"""
    return html
