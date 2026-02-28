import os
import json
import tempfile
from ui import load_css
load_css()
import streamlit as st

st.markdown(
    "<div class='acu-card'>"
    "<h2 style='margin:0'>ACU — Asesor</h2>"
    "<p class='acu-muted' style='margin:6px 0 0 0'>Diagnóstico de cartera vs perfil</p>"
    "</div>",
    unsafe_allow_html=True
)

st.markdown("<div class='acu-divider'></div>", unsafe_allow_html=True)
from ai_interpretation import interpretacion_basica
# IMPORTS de tu proyecto (como ya los venías usando en cloud)
from io_excel import read_portfolio_excel, write_analysis_json
from engine_v1 import run_analysis
from save_messages import save_messages_from_analysis_json
from report_html import generate_html_report
from narrative_v1 import build_client_messages

st.set_page_config(page_title="Asesor - Diagnóstico", layout="wide")
st.title("Asesor · Diagnóstico de Cartera")
st.caption("Acceso restringido. Subí el Excel del cliente y generá el reporte en 1 click.")

# ---- Password gate ----
st.sidebar.subheader("Acceso")

pwd = (st.sidebar.text_input("Contraseña del asesor", type="password") or "").strip()
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
perfil_declarado = st.sidebar.selectbox("Perfil declarado", ["Moderada", "Conservadora", "Agresiva"], index=0)

st.sidebar.subheader("Perfil del cliente (opcional)")
perfil_json = st.sidebar.file_uploader("Subir perfil_cliente.json", type=["json"])

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

            # Si querés: usar perfil implícito como alerta/mismatch (sin cambiar engine por ahora)
            analysis = run_analysis(payload, perfil_declarado=perfil_declarado)
            payload["analysis"] = analysis

            # Guardar outputs
            out_path = write_analysis_json(payload)
            out_dir = os.path.dirname(out_path)

            save_messages_from_analysis_json(out_path)
            html_path = generate_html_report(out_path)

            st.success(f"✅ Listo. Output generado en: {out_dir}")

            # Mostrar mismatch (si hay cuestionario)
            if perfil_implicito and perfil_implicito != perfil_declarado:
                st.error(f"⚠️ Mismatch de perfil: declarado **{perfil_declarado}** vs implícito **{perfil_implicito}**.")
            elif perfil_implicito:
                st.success(f"✅ Perfil consistente: declarado {perfil_declarado} = implícito {perfil_implicito}.")

            metrics = analysis["metrics"]
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Volatilidad", f"{metrics['VolPromedioCartera']:.1f}%")
            col2.metric("Score", f"{metrics['ScorePromedioCartera']:.1f}")
            col3.metric("Top 3", f"{metrics['ConcentracionTop3']*100:.0f}%")
            col4.metric("Top 1", f"{metrics['ConcentracionTop1']*100:.0f}%")
            col5.metric("HHI", f"{metrics['IndiceHerfindahl']:.2f}")

            st.subheader("⚠️ Alertas")
            alerts = analysis.get("alerts", [])
            if alerts:
                for a in alerts:
                    st.write("•", a["msg"])
            else:
                st.write("Sin alertas críticas.")

            st.subheader("✅ Recomendaciones")
            recs = analysis.get("recommendations", [])
            if recs:
                for r in recs:
                    st.write(f"**{r['title']}** — {r['detail']}")
            else:
                st.write("Sin recomendaciones automáticas.")

            st.subheader("💬 Mensajes listos")
            messages = build_client_messages(payload)
            st.text_area("WhatsApp", messages["whatsapp"], height=180)
            st.text_area("Email", f"Subject: {messages['email']['subject']}\n\n{messages['email']['body']}", height=240)

            st.subheader("📄 Descargas")
            with open(out_path, "r", encoding="utf-8") as f:
                st.download_button("Descargar analysis.json", f, file_name="analysis.json")
            with open(html_path, "r", encoding="utf-8") as f:
                st.download_button("Descargar report.html", f, file_name="report.html")

        except Exception as e:
            st.error(f"❌ Error: {e}")
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
