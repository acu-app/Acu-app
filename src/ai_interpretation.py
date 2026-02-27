from src.ai_interpretation import interpretacion_basica
def interpretacion_basica(perfil_data: dict) -> str:
    """
    Genera una interpretación simple (sin IA) a partir del JSON del cuestionario.
    Espera claves tipo: perfil_implicito, score, respuestas, etc.
    """

    perfil = perfil_data.get("perfil_implicito", "N/A")
    score = perfil_data.get("score", None)

    # Si guardás las respuestas en perfil_data["respuestas"]
    respuestas = perfil_data.get("respuestas", {})

    texto = []
    texto.append(f"Perfil implícito sugerido: **{perfil}**")
    if score is not None:
        texto.append(f"Puntaje total: **{score}**")

    # Ejemplo: mini explicación por horizonte (ajustalo a tus keys reales)
    # Si tu JSON guarda q2 como 'Menos de 2 años', etc:
    horizonte = respuestas.get("q2")
    if horizonte:
        texto.append(f"- Horizonte declarado: **{horizonte}**")

    # Mensaje final
    texto.append("")
    texto.append("**Nota:** Esta interpretación es orientativa y debe validarse con la cartera del cliente.")

    return "\n".join(texto)
