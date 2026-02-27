from src.ai_interpretation import interpretacion_basica
def interpretacion_basica(perfil_data: dict) -> str:
    perfil = perfil_data.get("perfil_implicito", "N/A")
    score = perfil_data.get("score", None)
    respuestas = perfil_data.get("respuestas", {})

    out = []
    out.append(f"Perfil implícito sugerido: **{perfil}**")
    if score is not None:
        out.append(f"Puntaje total: **{score}**")

    # ejemplo (si existe q2)
    if "q2" in respuestas:
        out.append(f"- Horizonte: **{respuestas['q2']}**")

    out.append("")
    out.append("**Nota:** Interpretación orientativa. Validar con la cartera del cliente.")
    return "\n".join(out)
