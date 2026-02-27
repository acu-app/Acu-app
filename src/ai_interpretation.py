from src.ai_interpretation import interpretacion_basica
def interpretacion_basica(perfil_payload: dict) -> str:
    perfil = perfil_payload.get("perfil_sugerido", "No definido")
    score = perfil_payload.get("score", "—")
    answers = perfil_payload.get("answers", {})

    motivos = []
    if "q2" in answers:
        motivos.append(f"Plazo declarado: {answers['q2']}")
    if "q3" in answers:
        motivos.append(f"Objetivo: {answers['q3']}")

    motivos_txt = " | ".join(motivos) if motivos else "Sin datos suficientes."

    return f"Perfil sugerido: {perfil} (score {score}). Motivos: {motivos_txt}."
