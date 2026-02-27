def interpretacion_basica(perfil_data: dict) -> str:
    perfil = perfil_data.get("perfil_implicito", "N/A")
    score = perfil_data.get("score", None)
    respuestas = perfil_data.get("respuestas", {})

    out = []
    out.append(f"Perfil implícito sugerido: {perfil}")

    if score is not None:
        out.append(f"Puntaje total: {score}")

    if "q2" in respuestas:
        out.append(f"Horizonte declarado: {respuestas['q2']}")

    out.append("")
    out.append("Interpretación orientativa. Validar con la cartera real del cliente.")

    return "\n".join(out)
