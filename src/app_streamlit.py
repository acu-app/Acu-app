import os
import sys

# Asegura que el root del repo esté en el path (Streamlit Cloud fix)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
import os
import tempfile
import json
import streamlit as st
from src.ui import load_css
load_css()
from src.io_excel import read_portfolio_excel, write_analysis_json
from src.engine_v1 import run_analysis
from src.save_messages import save_messages_from_analysis_json
from src.report_html import generate_html_report
from src.narrative_v1 import build_client_messages
def load_css():
    with open("src/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

st.set_page_config(page_title="ACU - Diagnóstico de Cartera", layout="wide")

st.title("ACU · Diagnóstico de Cartera (MVP)")
st.caption("Subí el Excel del cliente, generá diagnóstico, alertas, recomendaciones y mensajes listos.")

perfil = st.selectbox("Perfil considerado", ["Moderada", "Conservadora", "Agresiva"], index=0)

uploaded = st.file_uploader("Subir Excel (.xlsx)", type=["xlsx"])

if uploaded is not None:
    st.success("Archivo cargado. Listo para generar diagnóstico.")

    if st.button("Generar diagnóstico (1 click)"):
        # 1) Guardar archivo subido en un tmp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = tmp.name

        try:
            # 2) Leer Excel
            payload = read_portfolio_excel(tmp_path)

            # 3) Correr análisis
            analysis = run_analysis(payload, perfil_declarado=perfil)
            payload["analysis"] = analysis

            # 4) Guardar analysis.json en output/YYYY-MM-DD/
            out_path = write_analysis_json(payload)
            out_dir = os.path.dirname(out_path)

            # 5) Generar mensajes y guardarlos
            save_messages_from_analysis_json(out_path)

            # 6) Generar HTML report
            html_path = generate_html_report(out_path)

            st.success(f"✅ Listo. Output generado en: {out_dir}")

            # ---- Mostrar resultados en pantalla ----
            metrics = analysis["metrics"]
            alerts = analysis["alerts"]
            recs = analysis["recommendations"]
            scenarios = analysis["scenarios"]

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Volatilidad", f"{metrics['VolPromedioCartera']:.1f}%")
            col2.metric("Score", f"{metrics['ScorePromedioCartera']:.1f}")
            col3.metric("Top 3", f"{metrics['ConcentracionTop3']*100:.0f}%")
            col4.metric("Top 1", f"{metrics['ConcentracionTop1']*100:.0f}%")
            col5.metric("HHI", f"{metrics['IndiceHerfindahl']:.2f}")

            st.subheader("⚠️ Alertas")
            if alerts:
                for a in alerts:
                    st.write("•", a["msg"])
            else:
                st.write("Sin alertas críticas.")

            st.subheader("✅ Recomendaciones")
            if recs:
                for r in recs:
                    st.write(f"**{r['title']}** — {r['detail']}")
            else:
                st.write("Sin recomendaciones automáticas.")

            st.subheader("🧪 Escenarios (sensibilidad)")
            if scenarios:
                for s in scenarios:
                    st.write(f"**{s['label']}** → Vol: {s['metrics_after']['VolPromedioCartera']:.1f}%")
            else:
                st.write("Sin escenarios.")

            # ---- Mensajes listos ----
            st.subheader("💬 Mensajes listos para enviar")
            messages = build_client_messages(payload)

            st.text_area("WhatsApp", messages["whatsapp"], height=180)
            st.text_area("Email (subject + body)", f"Subject: {messages['email']['subject']}\n\n{messages['email']['body']}", height=240)
            st.text_area("Explicación simple", messages["simple"], height=160)

            # ---- Descargas ----
            st.subheader("📄 Descargas")
            with open(out_path, "r", encoding="utf-8") as f:
                st.download_button("Descargar analysis.json", f, file_name="analysis.json")

            with open(html_path, "r", encoding="utf-8") as f:
                st.download_button("Descargar report.html", f, file_name="report.html")

            st.info("Tip: el reporte HTML también queda guardado en la carpeta output del día.")

        except Exception as e:
            st.error(f"❌ Error: {e}")

        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
