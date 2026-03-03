import os
import json
import tempfile
import streamlit as st
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from ui import load_css
from ai_interpretation import interpretacion_basica
from io_excel import read_portfolio_excel, write_analysis_json
from engine_v1 import run_analysis
from save_messages import save_messages_from_analysis_json
from report_html import generate_html_report
from narrative_v1 import build_client_messages
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import io
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader
from src.utils.client_store import new_run_dir, save_run_artifacts, append_history, list_clients
from datetime import datetime
import os

client_ids = list_clients()



# Defaults para evitar NameError en reruns
client_id = None
portfolio_file = None
perfil_data = None
analysis = {}
alerts = []
client_ids = list_clients()

if not client_ids:
    st.warning("No hay clientes creados todavía.")
    st.stop()

client_id = st.selectbox("Seleccionar cliente", client_ids, key="client_id")

if "pdf_bytes" not in st.session_state:
    st.session_state["pdf_bytes"] = None
if "client_id" not in st.session_state:
    st.session_state["client_id"] = None


def build_portfolio_pdf(payload: dict, analysis: dict) -> bytes:
    metrics = analysis.get("metrics", {}) if isinstance(analysis, dict) else {}

    vol = metrics.get("VolPromedioCartera", 0)
    score = metrics.get("ScorePromedioCartera", 0)
    top3 = metrics.get("ConcentracionTop3", 0)
    top1 = metrics.get("ConcentracionTop1", 0)
    hhi = metrics.get("IndiceHerfindahl", 0)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    y = h - 60
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "AQ Capitals — Diagnóstico de Cartera")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Perfil declarado: {payload.get('perfil_declarado','-')}")
    y -= 20

    metrics = (analysis or {}).get("metrics", {})
    c.drawString(50, y, f"Volatilidad: {metrics.get('VolPromedioCartera','-')}")
    y -= 16
    c.drawString(50, y, f"Score: {metrics.get('ScorePromedioCartera','-')}")
    y -= 16
    c.drawString(50, y, f"Top 3: {metrics.get('ConcentracionTop3','-')}")
    y -= 16
    c.drawString(50, y, f"Top 1: {metrics.get('ConcentracionTop1','-')}")
    y -= 16
    c.drawString(50, y, f"HHI: {metrics.get('IndiceHerfindahl','-')}")
    y -= 26

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Alertas")
    y -= 18
    c.setFont("Helvetica", 10)
    def pct(v):
        return f"{v*100:.1f}%" if v <= 1 else f"{v:.1f}%"

    def num(v):
        if v is None:
            return "-"
        return f"{v:.2f}"

    # ---- DRAW ----
    draw(f"Volatilidad: {pct(vol)}")
    draw(f"Score: {score:.1f}")
    draw(f"Top 3: {pct(top3)}")
    draw(f"Top 1: {pct(top1)}")
    draw(f"HHI: {num(hhi)}")
    alerts = (analysis or {}).get("alerts", [])
    if not alerts:
        c.drawString(60, y, "- Sin alertas críticas.")
        y -= 14
    else:
        for a in alerts[:12]:
            msg = a.get("msg", str(a))
            c.drawString(60, y, f"- {msg[:110]}")
            y -= 14
            if y < 80:
                c.showPage()
                y = h - 60
                c.setFont("Helvetica", 10)

    c.showPage()
    c.save()
    return buf.getvalue()

def build_portfolio_pdf_bytes(payload, analysis, perfil_declarado, alerts):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    import io

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    margin = 50
    y = height - margin

    # -------- Helper draw --------
    def draw(txt, font_size=11, bold=False):
        nonlocal y
        txt = "" if txt is None else str(txt)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", font_size)
        c.drawString(margin, y, txt)
        y -= 18

    # -------- Helpers format --------
    def pct(v):
        if v is None:
            return "-"
        try:
            v = float(v)
        except:
            return "-"
        return f"{v*100:.1f}%" if v <= 1 else f"{v:.1f}%"

    def num(v):
        if v is None:
            return "-"
        try:
            return f"{float(v):.2f}"
        except:
            return "-"

    # -------- Extraer metrics --------
    metrics = analysis.get("metrics", {}) if isinstance(analysis, dict) else {}

    vol = metrics.get("VolPromedioCartera")
    score = metrics.get("ScorePromedioCartera")
    top3 = metrics.get("ConcentracionTop3")
    top1 = metrics.get("ConcentracionTop1")
    hhi = metrics.get("IndiceHerfindahl")

    # -------- Título --------
    draw("AQ Capitals — Diagnóstico de Cartera", 18, True)
    y -= 10

    draw(f"Perfil declarado: {perfil_declarado}", 12)
    y -= 10

    # -------- Métricas --------
    draw("Resumen cuantitativo", 14, True)
    y -= 5

    draw(f"Volatilidad: {pct(vol)}")
    draw(f"Score: {num(score)}")
    draw(f"Top 3: {pct(top3)}")
    draw(f"Top 1: {pct(top1)}")
    draw(f"HHI: {num(hhi)}")

    y -= 10
        # -------- Activos en cartera --------
        # -------- Activos en cartera --------
    y -= 10
    draw("Activos en cartera", 14, True)
    y -= 5

    def _pick_name(d: dict) -> str:
        for k in (
            "nombre", "activo", "instrumento", "especie", "descripcion",
            "ticker", "symbol", "name", "security", "asset"
        ):
            v = d.get(k)
            if v:
                s = str(v).strip()
                if s.lower() not in ("nan", "none", "-"):
                    return s

        # fallback: primer valor util
        for v in d.values():
            if v:
                s = str(v).strip()
                if s.lower() not in ("nan", "none", "-") and len(s) < 80:
                    return s

        return "Activo"

    rows = []
    # ---- sacar lista de activos desde payload ----
    candidates = []

    candidates = []

    if isinstance(payload, dict):
        # probá varias llaves típicas
        for k in ("activos", "assets", "positions", "posiciones", "holdings", "tenencias"):
            v = payload.get(k)
            if isinstance(v, list) and v:
                candidates = v
                break

        # fallback: si no está directo, a veces viene en payload["portfolio"]
        if not candidates:
            p = payload.get("portfolio")
            if isinstance(p, dict):
                for k in ("activos", "assets", "positions", "posiciones", "holdings", "tenencias"):
                    v = p.get(k)
                    if isinstance(v, list) and v:
                        candidates = v
                        break

    # si sigue vacío, al menos no rompe
    if not candidates:
        candidates = []



# si sigue vacío, al menos no rompe
    if not candidates:
        candidates = []

    def _to_float(x):
        if x is None:
            return None
        try:
            if isinstance(x, str):
                s = x.strip().replace("%", "").replace(",", ".")
                if s == "" or s.lower() in ("nan", "none", "-"):
                    return None
                return float(s)
            return float(x)
        except Exception:
            return None



    for it in candidates:
        if isinstance(it, dict):
            nombre = _pick_name(it)

            peso = (
                it.get("peso")
                or it.get("weight")
                or it.get("ponderacion")
                or it.get("%")
                or it.get("pct")
            )

            peso_f = _to_float(peso)

            monto = it.get("monto") or it.get("amount") or it.get("valor") or it.get("value")
            monto_f = _to_float(monto)

            moneda = it.get("moneda") or it.get("currency") or ""
            rows.append((str(nombre), peso_f, monto_f, str(moneda)))
        else:
            rows.append((str(it), None, None, ""))

    
    # Orden: por peso desc si existe
    rows.sort(key=lambda r: (r[1] is not None, r[1] or 0), reverse=True)

    if not rows:
        draw("No se encontraron activos en el payload.")
    else:
        # mostramos hasta 25 para no romper el layout
        max_items = 25  
        for i, (nombre, peso_f, monto_f, moneda) in enumerate(rows[:max_items], start=1):
            parts = [f"{i}. {nombre}"]
            if peso_f is not None:
                parts.append(f"({pct(peso_f)})")
            if monto_f is not None:
                parts.append(f"- {monto_f:,.2f} {moneda}".strip())
            draw(" ".join(parts))

        if len(rows) > max_items:
            draw(f"... y {len(rows) - max_items} activos más.")

    # -------- Alertas --------
    draw("Alertas detectadas", 14, True)
    y -= 5

    if alerts:
        for a in alerts:
            if isinstance(a, dict): 
                msg = a.get("msg") or str(a)
            else:
                msg = str(a)
            draw(f"- {msg}")
    else:
        draw("No se detectaron alertas críticas.")   

    c.save()
    buffer.seek(0)
    # -------- Pie Chart Distribución por Peso --------
    draw(f"DEBUG rows: {len(rows)}")
    y -= 10
    # Helper interno para generar el gráfico
    def _make_pie_chart_png(labels, values, title="Distribución por peso (Top 10)"):
        data = [(l, v) for l, v in zip(labels, values) if v is not None and v > 0]
        if not data:
            return None

        labels, values = zip(*data)

        fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=200)
        ax.pie(values, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        ax.set_title(title)

        ax.legend(labels, loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=7)

        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf

    # Tomamos Top 10 por peso
    top_rows = [r for r in rows if r[1] is not None and r[1] > 0][:10]

    if top_rows:
        labels = [r[0] for r in top_rows]
        values = [r[1] for r in top_rows]

        pie_buf = _make_pie_chart_png(labels, values)

        if pie_buf:
            draw("Distribución por peso (Top 10)", 14, True)
            y -= 10

            img = ImageReader(pie_buf)
            img_w = 320
            img_h = 240

            # Si no entra en la página, salto
            if y - img_h < 60:
                c.showPage()
                y = height - margin

            c.drawImage(
                img,
                margin,
                y - img_h,
                width=img_w,
                height=img_h,
                preserveAspectRatio=True,
                mask="auto",
            )

            y -= (img_h + 20)
    else:
        draw("Distribución por peso: sin datos suficientes.")
        y -= 10
    draw(f"DEBUG top_rows: {len(top_rows)}")
    y -= 10
    return buffer.getvalue()
pdf_data = st.session_state.get("pdf_bytes")
if pdf_data and st.button("💾 Guardar diagnóstico en historial"):

    run = new_run_dir(client_id)
    run_id = run["run_id"]
    run_base = run["run_base"]

    metrics = analysis.get("metrics", {}) if isinstance(analysis, dict) else {}

    summary = {
        "client_id": client_id,
        "run_id": run_id,
        "score": metrics.get("ScorePromedioCartera"),
        "vol": metrics.get("VolPromedioCartera"),
        "top1": metrics.get("ConcentracionTop1"),
        "top3": metrics.get("ConcentracionTop3"),
        "hhi": metrics.get("HHI"),
        "alerts_count": len(alerts) if alerts else 0,
    }

    save_run_artifacts(
        run_base=run_base,
        excel_bytes=portfolio_file.getvalue(),
        perfil_data=perfil_data if isinstance(perfil_data, dict) else {},
        pdf_bytes=pdf_data,
        summary=summary,
    )

    append_history(client_id, {"event": "RUN_SAVED", **summary})

    st.success(f"Diagnóstico guardado correctamente (Run: {run_id})")







# ✅ Siempre primero
st.set_page_config(page_title="AQ Capitals · Asesor", layout="wide")

# ✅ Después CSS
load_css()

# ✅ Header AQ (solo uno)
st.markdown("""
<div class="aq-hero">
  <div class="aq-hero-title">AQ Capitals · Portfolio Intelligence</div>
  <div class="aq-hero-sub">Diagnóstico de alineación perfil vs cartera en segundos.</div>

  <div class="aq-badges">
    <span class="aq-badge">Análisis Técnico</span>
    <span class="aq-badge">Alertas</span>
    <span class="aq-badge">Texto listo para cliente</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Acceso restringido. Subí el Excel del cliente y generá el reporte en 1 click.")
# ---- Password gate ----
st.sidebar.subheader("Acceso")

pwd = (
    st.sidebar.text_input(
        "Contraseña del asesor",
         type="password") or "").strip()
ADVISOR_PASSWORD = (st.secrets.get("ADVISOR_PASSWORD", "") or "").strip()

if ADVISOR_PASSWORD == "":
    st.error("Falta configurar ADVISOR_PASSWORD en Streamlit Secrets.")
    st.stop()

if pwd == "":
    st.info("Ingresá la contraseña para acceder al diagnóstico.")
    st.stop()

if pwd != ADVISOR_PASSWORD:
    st.error("Contraseña incorrecta.")
    st.stop()

st.success("✅ Acceso concedido")
# ---- Inputs ----
st.sidebar.subheader("Perfil")
perfil_declarado = st.sidebar.selectbox(
    "Perfil declarado", [
        "Moderada", "Conservadora", "Agresiva"], index=0)

st.sidebar.subheader("Perfil del cliente (opcional)")
perfil_json = st.sidebar.file_uploader(
    "Subir perfil_cliente.json", type=["json"])

perfil_implicito = None

try:
    if perfil_json is None:
        perfil_data = {}
    elif isinstance(perfil_json, dict):
        perfil_data = perfil_json
    elif hasattr(perfil_json, "getvalue"):
        raw = perfil_json.getvalue()
        if isinstance(raw, (bytes, bytearray)):
            perfil_data = json.loads(raw.decode("utf-8"))
        else:
            perfil_data = json.loads(raw)
    else:
        perfil_data = {}

    perfil_implicito = perfil_data.get("perfil_implicito")

except Exception as e:
    st.sidebar.error(f"JSON inválido: {e}")
    perfil_implicito = None




uploaded = st.file_uploader("Subir Excel del cliente (.xlsx)", type=["xlsx"])

if uploaded is not None:
    st.success("Archivo cargado. Listo para generar diagnóstico.")

if st.button("Generar diagnóstico (1 click)"):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = tmp.name

    try:
        payload = read_portfolio_excel(tmp_path)
        analysis = run_analysis(payload, perfil_declarado=perfil_declarado)
        payload["analysis"] = analysis
        alerts = []
        if isinstance(analysis, dict):
            alerts = analysis.get("alerts", []) or []

        alerts = []
        if isinstance(analysis, dict):
           alerts = analysis.get("alerts", []) or []

        st.session_state["pdf_bytes"] = build_portfolio_pdf_bytes(
           payload,
           analysis,
           perfil_declarado,
           alerts
)
        out_path = write_analysis_json(payload)
        out_dir = os.path.dirname(out_path)

        save_messages_from_analysis_json(out_path)
        html_path = generate_html_report(out_path)

        st.success(f"✅ Listo. Output generado en: {out_dir}")

        perfil_implicito = analysis.get("perfil_implicito") if isinstance(analysis, dict) else None
        if perfil_implicito and perfil_implicito != perfil_declarado:
            st.error(
                f"⚠️ Mismatch de perfil: declarado **{perfil_declarado}** vs implícito **{perfil_implicito}**."
            )
        elif perfil_implicito:
            st.success(
                f"✅ Perfil consistente: declarado **{perfil_declarado}** = implícito **{perfil_implicito}**."
            )

        metrics = analysis.get("metrics", {}) if isinstance(analysis, dict) else {}
        if metrics:
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Volatilidad", f"{metrics.get('VolPromedioCartera', 0):.1f}%")
            col2.metric("Score", f"{metrics.get('ScorePromedioCartera', 0):.1f}")
            col3.metric("Top 3", f"{metrics.get('ConcentracionTop3', 0)*100:.0f}%")
            col4.metric("Top 1", f"{metrics.get('ConcentracionTop1', 0)*100:.0f}%")
            col5.metric("HHI", f"{metrics.get('IndiceHerfindahl', 0):.2f}")

        st.subheader("⚠️ Alertas")
        alerts = analysis.get("alerts", []) if isinstance(analysis, dict) else []
        if alerts:
            for a in alerts:
                clean = str(a.get("msg", str(a))) if isinstance(a, dict) else str(a)
                clean = clean.split(" (")[0]   # corta todo lo que venga desde " ("
                st.write("•", clean)
        else:
            st.write("Sin alertas críticas.")
            # === Executive Summary + Plan de acción (AQ Capitals) ===
        st.subheader("📌 Resumen Ejecutivo")

        vol_raw = float(metrics.get("VolPromedioCartera", 0))
        vol_pct = vol_raw if vol_raw > 1 else vol_raw * 100   # 19.2 -> 19.2 | 0.192 -> 19.2
        vol = vol_pct / 100.0                                 # para comparaciones internas
        score_port = float(metrics.get("ScorePromedioCartera", 0))
        top3 = float(metrics.get("ConcentracionTop3", 0))
        top1 = float(metrics.get("ConcentracionTop1", 0))
        hhi = float(metrics.get("IndiceHerfindahl", 0))

        riesgos = []
        if top1 > 0.25:
            riesgos.append("Concentración elevada en el activo principal (Top1 > 25%).")
        if top3 > 0.55:
            riesgos.append("Cartera dominada por los tres principales activos (Top3 > 55%).")
        if hhi > 0.18:
            riesgos.append("Diversificación estructural baja (HHI elevado).")
        if vol > 0.18:
            riesgos.append("Nivel de volatilidad elevado respecto a estándares conservadores.")

        if not riesgos:
            riesgos = ["No se detectan riesgos críticos bajo los umbrales actuales."]

        acciones = []
        if top1 > 0.25:
            acciones.append("Reducir exposición del activo principal y redistribuir en posiciones complementarias.")
        if top3 > 0.55:
            acciones.append("Aumentar diversificación sectorial o por clase de activo.")
        if hhi > 0.18:
            acciones.append("Optimizar distribución para mejorar estabilidad ante escenarios adversos.")
        if not acciones:
            acciones = ["Mantener estrategia actual con monitoreo periódico."]

        resumen = (
            f"La cartera presenta un score promedio de {score_port:.1f} "
            f"y volatilidad estimada de {vol_pct:.1f}%. "
            f"Concentración Top3: {top3*100:.0f}% | Top1: {top1*100:.0f}% (HHI {hhi:.2f})."
        )

        st.markdown(f"**AQ Capitals | Diagnóstico Cuantitativo:** {resumen}")

        st.markdown("**Riesgos principales identificados**")
        for r in riesgos:
            st.write("•", r)

        st.markdown("**Lineamientos estratégicos sugeridos**")
        for a in acciones:
            st.write("•", a)

        st.subheader("✉️ Texto listo para enviar al cliente")

        whatsapp = (
            f"Hola, ya revisé tu cartera. "
            f"Hoy presenta una volatilidad estimada de {vol_pct:.1f}% "
            f"y concentración Top3 del {top3*100:.0f}%. "
            f"Te propongo revisar juntos ajustes para optimizar diversificación "
            f"y alinearlo con tu perfil {perfil_declarado}. "
            f"¿Coordinamos una llamada breve esta semana?"
        )

        email = (
            f"Asunto: Diagnóstico de Cartera – AQ Capitals\n\n"
            f"Estimado/a,\n\n"
            f"A continuación, un resumen ejecutivo del análisis:\n"
            f"- Volatilidad estimada: {vol*100:.1f}%\n"
            f"- Concentración Top3: {top3*100:.0f}%\n"
            f"- Concentración Top1: {top1*100:.0f}%\n"
            f"- Índice de Diversificación (HHI): {hhi:.2f}\n\n"
            f"Principales observaciones:\n"
            + "\n".join([f"- {r}" for r in riesgos]) +
            f"\n\nLineamientos sugeridos:\n"
            + "\n".join([f"- {a}" for a in acciones]) +
            f"\n\nQuedo a disposición para coordinar una revisión estratégica.\n\n"
            f"Saludos,\nAQ Capitals"
        )

        st.text_area("WhatsApp", whatsapp, height=120)
        st.text_area("Email", email, height=240)
        # ===== PDF descargable (AQ Capitals) =====



    except Exception as e:
        st.exception(e)
st.divider()


if isinstance(pdf_data, bytes) and len(pdf_data) > 0:
    st.download_button(
        "📄 Descargar reporte PDF (AQ Capitals)",
        data=pdf_data,
        file_name="AQCapitals_Diagnostico.pdf",
        mime="application/pdf",
        key="download_pdf",
    )
else:
    st.info("Primero generá el reporte para habilitar la descarga.")
if (
    client_id
    and portfolio_file is not None
    and "pdf_bytes" in st.session_state
    and st.session_state["pdf_bytes"] is not None
):
    run = new_run_dir(client_id)  # crea /runs/<run_id>/
    run_id = run["run_id"]
    run_base = run["run_base"]

    metrics = analysis.get("metrics", {}) if isinstance(analysis, dict) else {}
    summary = {
        "client_id": client_id,
        "run_id": run_id,
        "score": metrics.get("ScorePromedioCartera"),
        "vol": metrics.get("VolPromedioCartera"),
        "top1": metrics.get("ConcentracionTop1"),
        "top3": metrics.get("ConcentracionTop3"),
        "alerts_count": len(alerts) if alerts else 0,
    }

    save_run_artifacts(
        run_base=run_base,
        excel_bytes=portfolio_file.getvalue(),
        perfil_data=perfil_data if isinstance(perfil_data, dict) else None,
        pdf_bytes=st.session_state["pdf_bytes"],
        summary=summary,
    )
    append_history(client_id, {"event": "diagnostico_guardado", **summary})
    st.success(f"Diagnóstico guardado para {client_id} (run: {run_id})")
pdf_data = st.session_state.get("pdf_bytes")

st.write("DEBUG", {
    "client_id": st.session_state.get("diagnostico_client_id"),
    "portfolio_uploaded": portfolio_file is not None,
    "pdf_key_exists": "pdf_bytes" in st.session_state,
    "pdf_type": str(type(pdf_data)),
    "pdf_len": len(pdf_data) if isinstance(pdf_data, (bytes, bytearray)) else None,
})
