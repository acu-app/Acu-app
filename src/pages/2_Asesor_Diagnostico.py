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

def build_portfolio_pdf_bytes(
    brand_title,
    perfil_declarado,
    metrics,
    alerts,
):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    x = 2 * cm
    y = height - 2 * cm
    line = 0.6 * cm

    def draw(txt, font_size=11, bold=False):
        nonlocal y
        txt = "" if txt is None else str(txt)   # <- CLAVE: fuerza texto siempre
        c.setFont("Helvetica-Bold" if bold else "Helvetica", font_size)
        c.drawString(margin, y, txt)
        y -= 14
    def pct(v):
        if v is None:
            return "-"
        return f"{v*100:.1f}%"

    def num(v):
        if v is None:
            return "-"
        return f"{v:.2f}"

    draw(f"Volatilidad: {pct(vol)}")
    draw(f"Score: {score:.1f}" if score is not None else "Score: -")
    draw(f"Top 3: {pct(top3)}")
    draw(f"Top 1: {pct(top1)}")
    draw(f"HHI: {num(hhi)}")

    y -= 0.5 * cm
    draw("Alertas", 14, True)

    if alerts:
        for a in alerts:
            draw(f"• {a}")
    else:
        draw("Sin alertas críticas.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()





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

if "pdf_bytes" in st.session_state:
    st.download_button(
        "📄 Descargar reporte PDF (AQ Capitals)",
        data=st.session_state["pdf_bytes"],
        file_name="AQCapitals_Diagnostico.pdf",
        mime="application/pdf",
    )
