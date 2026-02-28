import json
import streamlit as st
from profile_report_html import generate_profile_html
from ui import load_css
load_css()
st.set_page_config(page_title="Cuestionario de Perfil", layout="centered")
st.title("Cuestionario de Perfil de Inversión")
st.caption("Completá este cuestionario. Al final vas a poder descargar el resultado para enviárselo a tu asesor.")

def score_to_profile(score: int) -> str:
    if score <= 6:
        return "Conservadora"
    elif score <= 12:
        return "Moderada"
    else:
        return "Agresiva"

# Preguntas (6)
q1 = st.radio("1) Si tu cartera cae 20% en un año, ¿qué hacés?",
             ["Vendo todo", "Espero y mantengo", "Compro más (aprovecho la baja)"])
q2 = st.radio("2) ¿Cuánto tiempo podés mantener tu inversión sin tocarla?",
             ["Menos de 2 años", "Entre 2 y 5 años", "Más de 5 años"])
q3 = st.radio("3) ¿Qué priorizás?",
             ["Preservar capital", "Equilibrio", "Crecimiento"])
q4 = st.radio("4) ¿Invertiste antes en acciones/ETFs?",
             ["No", "Algo / pocas veces", "Sí, regularmente"])
q5 = st.radio("5) ¿Qué porcentaje de tu patrimonio representa esta inversión?",
             ["Más del 70%", "Entre 40% y 70%", "Menos del 40%"])
q6 = st.radio("6) ¿Te sentís cómodo con volatilidad alta (subidas/bajadas)?",
             ["No", "Moderada", "Sí"])

# Scoring
map_q1 = {"Vendo todo": 0, "Espero y mantengo": 2, "Compro más (aprovecho la baja)": 3}
map_q2 = {"Menos de 2 años": 0, "Entre 2 y 5 años": 2, "Más de 5 años": 3}
map_q3 = {"Preservar capital": 0, "Equilibrio": 2, "Crecimiento": 3}
map_q4 = {"No": 0, "Algo / pocas veces": 2, "Sí, regularmente": 3}
map_q5 = {"Más del 70%": 0, "Entre 40% y 70%": 2, "Menos del 40%": 3}
map_q6 = {"No": 0, "Moderada": 2, "Sí": 3}

score = (
    map_q1[q1] + map_q2[q2] + map_q3[q3] +
    map_q4[q4] + map_q5[q5] + map_q6[q6]
)
perfil = score_to_profile(score)

st.divider()
st.subheader("Resultado")
st.metric("Perfil sugerido", perfil)
st.write(f"Puntaje total: **{score}** (0 a 18)")

result_payload = {
    "perfil_implicito": perfil,
    "score": score,
    "answers": {
        "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5, "q6": q6
    }
}

st.download_button(
    "Descargar resultado (para enviar al asesor)",
    data=json.dumps(result_payload, ensure_ascii=False, indent=2).encode("utf-8"),
    file_name="perfil_cliente.json",
    mime="application/json"
)
# ---- HTML descargable (para el cliente) ----
html_report = generate_profile_html(result_payload)

st.download_button(
    "⬇️ Descargar perfil en formato presentable (HTML)",
    data=html_report,
    file_name="perfil_cliente.html",
    mime="text/html"
)

st.info("Para generar PDF: abrí el HTML descargado y presioná Ctrl+P (⌘+P en Mac) → Guardar como PDF.")


st.caption("Privacidad: este cuestionario no constituye recomendación de inversión. El asesor interpretará el resultado junto con la cartera.")
