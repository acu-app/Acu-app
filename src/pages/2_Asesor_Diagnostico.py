import os
import json
import tempfile
import streamlit as st

from ui import load_css
from ai_interpretation import interpretacion_basica
from io_excel import read_portfolio_excel, write_analysis_json
from engine_v1 import run_analysis
from save_messages import save_messages_from_analysis_json
from report_html import generate_html_report
from narrative_v1 import build_client_messages

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

if perfil_json is not None:
    try:
        perfil_data = json.loads(perfil_json.getvalue().decode("utf-8"))
        perfil_implicito = perfil_data.get("perfil_implicito")

        st.sidebar.success(
            f"Perfil implícito: {perfil_implicito} (score {perfil_data.get('score')})"
        )

        st.subheader("Interpretación (solo asesor)")
        interpretacion_txt = interpretacion_basica(perfil_data)
        st.write(interpretacion_txt)

    except Exception as e:
        st.sidebar.error(f"JSON inválido: {e}")


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
                st.write("•", a.get("msg", str(a)))
        else:
            st.write("Sin alertas críticas.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
