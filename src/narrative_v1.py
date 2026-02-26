from __future__ import annotations

from typing import Dict, List


def _pct(x: float) -> str:
    return f"{x*100:.0f}%"


def _fmt_vol(x: float) -> str:
    # tu vol parece venir como "19.2" = 19.2%
    return f"{x:.1f}%"


def build_client_messages(payload: dict) -> dict:
    """
    Genera textos listos para copiar/pegar:
    - WhatsApp (corto)
    - Email (formal)
    - Simple (explicación muy fácil)
    Requiere: payload['analysis'] ya calculado por engine_v1.
    """
    analysis = payload.get("analysis", {})
    metrics = analysis.get("metrics", {})
    alerts: List[dict] = analysis.get("alerts", [])
    recs: List[dict] = analysis.get("recommendations", [])
    perfil = analysis.get("perfil_declarado") or "—"

    score = metrics.get("ScorePromedioCartera", None)
    vol = metrics.get("VolPromedioCartera", None)
    top1 = metrics.get("ConcentracionTop1", 0.0)
    top3 = metrics.get("ConcentracionTop3", 0.0)

    exp_pais = metrics.get("ExposicionPorPais", {})
    # top país
    top_pais = next(iter(exp_pais.items()), (None, None))

    # Alertas principales (texto)
    alert_lines = [f"- {a.get('msg')}" for a in alerts[:3]]

    # Recomendación principal (texto)
    main_rec = recs[0]["detail"] if recs else None

    # --- WhatsApp (corto) ---
    wa_lines = []
    wa_lines.append("Hola! Te comparto un resumen rápido de la cartera:")
    if vol is not None:
        wa_lines.append(f"• Riesgo (volatilidad promedio): {_fmt_vol(vol)}")
    if top3 is not None:
        wa_lines.append(f"• Concentración Top 3: {_pct(top3)}")
    if top_pais[0] is not None:
        wa_lines.append(f"• Exposición principal: {top_pais[0]} {_pct(top_pais[1])}")
    if perfil != "—":
        wa_lines.append(f"• Perfil considerado: {perfil}")

    if alerts:
        wa_lines.append("⚠️ Alertas:")
        wa_lines.extend(alert_lines)

    if main_rec:
        wa_lines.append("✅ Sugerencia:")
        wa_lines.append(f"• {main_rec}")

    whatsapp = "\n".join(wa_lines)

    # --- Email (formal) ---
    subject = "Resumen de cartera y próximos pasos"
    email_lines = []
    email_lines.append("Hola,")
    email_lines.append("")
    email_lines.append("Comparto el diagnóstico actualizado de la cartera en base a los datos provistos.")
    email_lines.append("")
    if vol is not None or top3 is not None:
        email_lines.append("Métricas principales:")
        if vol is not None:
            email_lines.append(f"- Volatilidad promedio ponderada: {_fmt_vol(vol)}")
        email_lines.append(f"- Concentración Top 3: {_pct(top3)}")
        email_lines.append(f"- Mayor posición individual (Top 1): {_pct(top1)}")
        if top_pais[0] is not None:
            email_lines.append(f"- Exposición geográfica principal: {top_pais[0]} {_pct(top_pais[1])}")
        if perfil != "—":
            email_lines.append(f"- Perfil considerado: {perfil}")
        email_lines.append("")

    if alerts:
        email_lines.append("Alertas detectadas:")
        for a in alerts[:5]:
            email_lines.append(f"- {a.get('msg')}")
        email_lines.append("")

    if recs:
        email_lines.append("Recomendaciones accionables (por reglas):")
        for r in recs[:2]:
            email_lines.append(f"- {r.get('detail')}")
        email_lines.append("")

    email_lines.append("Si querés, puedo simular escenarios (risk-off / shock por país) para ver sensibilidad de la cartera y validar el rebalanceo.")
    email_lines.append("")
    email_lines.append("Saludos,")
    email_body = "\n".join(email_lines)

    # --- Simple (muy fácil) ---
    simple_lines = []
    simple_lines.append("Resumen simple:")
    if top3 is not None:
        simple_lines.append(f"- Hoy la cartera está bastante concentrada: los 3 activos principales pesan {_pct(top3)}.")
    if vol is not None:
        simple_lines.append(f"- El nivel de movimiento esperado (riesgo) es aprox. {_fmt_vol(vol)}.")
    if top_pais[0] is not None:
        simple_lines.append(f"- La mayor parte está expuesta a {top_pais[0]} ({_pct(top_pais[1])}).")
    if main_rec:
        simple_lines.append(f"- Próximo paso sugerido: {main_rec}")
    simple = "\n".join(simple_lines)

    return {
        "whatsapp": whatsapp,
        "email": {"subject": subject, "body": email_body},
        "simple": simple,
    }
