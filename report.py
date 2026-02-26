from pathlib import Path
from datetime import datetime

def save_html(output_dir: Path, cliente: dict, metrics: dict, df_top):
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "reporte_cliente.html"

    rows = ""
    for _, r in df_top.iterrows():
        rows += f"""
        <tr>
          <td>{r.get('Activo','')}</td>
          <td>{r.get('Tipo','')}</td>
          <td>{r.get('Pais','')}</td>
          <td>{r.get('ISO','')}</td>
          <td>{r.get('Peso',0):.4f}</td>
          <td>{r.get('ScoreActivoFinal',0):.2f}</td>
        </tr>
        """

    html = f"""
    <html>
    <body>
    <h1>Reporte de Cartera – {cliente.get('Nombre','Cliente')}</h1>
    <p>Generado: {datetime.now()}</p>

    <h3>Métricas</h3>
    <ul>
      <li>Score promedio: {metrics['score_avg']:.2f}</li>
      <li>Concentración Top 3: {metrics['top3']*100:.0f}%</li>
    </ul>

    <h3>Top holdings</h3>
    <table border="1">
      <tr>
        <th>Activo</th><th>Tipo</th><th>Pais</th><th>ISO</th><th>Peso</th><th>Score</th>
      </tr>
      {rows}
    </table>

    </body>
    </html>
    """

    out.write_text(html, encoding="utf-8")
    return out
