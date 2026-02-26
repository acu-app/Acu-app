from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, Tuple
import copy


DEFAULT_THRESHOLDS = {
    "top1_max": 0.25,
    "top3_max": 0.55,
    "hhi_max": 0.18,
    "country_max": 0.60,
    "vol_profile_limits": {  # volatilidad en %
        "Conservadora": 12.0,
        "Moderada": 18.0,
        "Agresiva": 25.0,
    },
}

DEFAULT_SCENARIOS = {
    "risk_off": {"type": "multiply_vol", "multiplier": 1.30, "label": "Risk-off (Vol +30%)"},
    "shock_arg": {"type": "multiply_vol_by_country", "country": "Argentina", "multiplier": 1.40, "label": "Shock Argentina (Vol ARG +40%)"},
    "shock_usa": {"type": "multiply_vol_by_country", "country": "USA", "multiplier": 1.20, "label": "Shock USA (Vol USA +20%)"},
}


def _safe_float(x) -> float:
    try:
        return float(x)
    except Exception:
        return float("nan")


def _group_weights(activos: List[dict], key: str) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for a in activos:
        k = str(a.get(key, "")).strip() if a.get(key) is not None else ""
        w = _safe_float(a.get("Peso"))
        if k == "" or w != w:
            continue
        out[k] = out.get(k, 0.0) + w
    # ordenar desc
    return dict(sorted(out.items(), key=lambda kv: kv[1], reverse=True))


def _top_n_holdings(activos: List[dict], n: int = 10) -> List[dict]:
    sorted_a = sorted(activos, key=lambda a: _safe_float(a.get("Peso")), reverse=True)
    out = []
    for a in sorted_a[:n]:
        out.append(
            {
                "Activo": a.get("Activo"),
                "Tipo": a.get("Tipo"),
                "Pais": a.get("Pais"),
                "Moneda": a.get("Moneda"),
                "Peso": _safe_float(a.get("Peso")),
                "VolatilidadFinal": _safe_float(a.get("VolatilidadFinal")),
                "ScoreActivoFinal": _safe_float(a.get("ScoreActivoFinal")),
            }
        )
    return out


def compute_metrics(activos: List[dict]) -> dict:
    # Promedios ponderados
    score_w = 0.0
    vol_w = 0.0
    country_ctx_w = 0.0
    country_ctx_ok = True

    hhi = 0.0
    weights_sum = 0.0

    for a in activos:
        w = _safe_float(a.get("Peso"))
        if w != w:
            continue
        weights_sum += w
        hhi += w * w

        s = _safe_float(a.get("ScoreActivoFinal"))
        v = _safe_float(a.get("VolatilidadFinal"))
        if s == s:
            score_w += w * s
        if v == v:
            vol_w += w * v

        c = a.get("CountryContextScore", None)
        if c is None:
            country_ctx_ok = False
        else:
            cf = _safe_float(c)
            if cf == cf:
                country_ctx_w += w * cf

    # Top1 / Top3
    weights_sorted = sorted([_safe_float(a.get("Peso")) for a in activos if _safe_float(a.get("Peso")) == _safe_float(a.get("Peso"))], reverse=True)
    top1 = weights_sorted[0] if weights_sorted else 0.0
    top3 = sum(weights_sorted[:3]) if len(weights_sorted) >= 3 else sum(weights_sorted)

    exposicion_pais = _group_weights(activos, "Pais")
    exposicion_tipo = _group_weights(activos, "Tipo")
    exposicion_moneda = _group_weights(activos, "Moneda")

    metrics = {
        "ScorePromedioCartera": score_w,
        "VolPromedioCartera": vol_w,  # en % (como tu Excel)
        "ConcentracionTop1": top1,
        "ConcentracionTop3": top3,
        "IndiceHerfindahl": hhi,
        "ExposicionPorPais": exposicion_pais,
        "ExposicionPorTipo": exposicion_tipo,
        "ExposicionPorMoneda": exposicion_moneda,
    }

    if country_ctx_ok:
        metrics["RiesgoPaisPromedioPonderado"] = country_ctx_w

    return metrics


def generate_alerts(metrics: dict, perfil_declarado: str | None, thresholds: dict) -> List[dict]:
    alerts: List[dict] = []

    top1 = metrics["ConcentracionTop1"]
    top3 = metrics["ConcentracionTop3"]
    hhi = metrics["IndiceHerfindahl"]
    vol = metrics["VolPromedioCartera"]

    if top1 > thresholds["top1_max"]:
        alerts.append({"type": "concentracion_top1", "severity": "alta", "msg": f"Concentración alta en un activo (Top1 {top1:.0%} > {thresholds['top1_max']:.0%})."})

    if top3 > thresholds["top3_max"]:
        alerts.append({"type": "concentracion_top3", "severity": "alta", "msg": f"Cartera dominada por Top3 (Top3 {top3:.0%} > {thresholds['top3_max']:.0%})."})

    if hhi > thresholds["hhi_max"]:
        alerts.append({"type": "hhi", "severity": "media", "msg": f"Diversificación baja (HHI {hhi:.0%} > {thresholds['hhi_max']:.0%})."})

    # concentración por país
    for pais, w in list(metrics["ExposicionPorPais"].items())[:1]:
        if w > thresholds["country_max"]:
            alerts.append({"type": "country_concentration", "severity": "media", "msg": f"Concentración geográfica alta en {pais} ({w:.0%} > {thresholds['country_max']:.0%})."})
        break

    # mismatch de perfil vs volatilidad
    if perfil_declarado:
        limits = thresholds["vol_profile_limits"]
        if perfil_declarado in limits and vol > limits[perfil_declarado]:
            alerts.append({"type": "perfil_mismatch", "severity": "alta", "msg": f"Volatilidad {vol:.1f}% alta para perfil {perfil_declarado} (umbral {limits[perfil_declarado]:.1f}%)."})

    # ordenar: alta primero
    sev_order = {"alta": 0, "media": 1, "baja": 2}
    alerts.sort(key=lambda a: sev_order.get(a["severity"], 9))
    return alerts[:5]


def recommend_rebalancing(activos: List[dict], metrics: dict, thresholds: dict) -> List[dict]:
    """
    Reglas v1:
    - Si Top1 > top1_max: bajar el Top1 al límite y redistribuir proporcionalmente en el resto.
    - Si Top3 > top3_max: bajar el Top1 y Top2 hasta reducir Top3 (simple).
    """
    recs: List[dict] = []

    # ordenar por peso
    sorted_a = sorted(activos, key=lambda a: _safe_float(a.get("Peso")), reverse=True)
    if not sorted_a:
        return recs

    top1_max = thresholds["top1_max"]
    top3_max = thresholds["top3_max"]

    top1 = metrics["ConcentracionTop1"]
    top3 = metrics["ConcentracionTop3"]

    # Helper: redistribuir delta al resto proporcionalmente
    def redistribute(activos_local: List[dict], idx_reduce: List[int], deltas: List[float]) -> List[dict]:
        new = copy.deepcopy(activos_local)
        # reducir
        total_delta = 0.0
        for idx, d in zip(idx_reduce, deltas):
            new[idx]["Peso"] = _safe_float(new[idx]["Peso"]) - d
            total_delta += d

        # distribuir en el resto
        rest_indices = [i for i in range(len(new)) if i not in idx_reduce]
        rest_sum = sum(_safe_float(new[i]["Peso"]) for i in rest_indices)
        if rest_sum <= 0:
            return new

        for i in rest_indices:
            w = _safe_float(new[i]["Peso"])
            new[i]["Peso"] = w + total_delta * (w / rest_sum)

        return new

    # Regla Top1
    if top1 > top1_max:
        exceso = top1 - top1_max
        propuesta = redistribute(sorted_a, [0], [exceso])
        recs.append({
            "rule": "cap_top1",
            "title": "Reducir concentración del principal activo",
            "detail": f"Bajar {sorted_a[0].get('Activo')} de {top1:.0%} a {top1_max:.0%} y redistribuir el excedente en el resto.",
            "proposed_weights_preview": [{"Activo": a.get("Activo"), "Peso": _safe_float(a.get("Peso"))} for a in propuesta[:6]],
        })

    # Regla Top3 (simple)
    if top3 > top3_max and len(sorted_a) >= 3:
        exceso_total = top3 - top3_max
        # reducimos 60% del exceso desde top1, 40% desde top2 (heurística simple)
        d1 = exceso_total * 0.6
        d2 = exceso_total * 0.4
        propuesta = redistribute(sorted_a, [0, 1], [d1, d2])
        recs.append({
            "rule": "cap_top3",
            "title": "Bajar dominancia del Top 3",
            "detail": f"Reducir peso de los 2 activos más grandes para llevar Top3 a ~{top3_max:.0%} y redistribuir al resto.",
            "proposed_weights_preview": [{"Activo": a.get("Activo"), "Peso": _safe_float(a.get("Peso"))} for a in propuesta[:6]],
        })

    return recs[:3]


def apply_scenario(activos: List[dict], scenario: dict) -> List[dict]:
    new = copy.deepcopy(activos)
    stype = scenario.get("type")

    if stype == "multiply_vol":
        m = float(scenario["multiplier"])
        for a in new:
            v = _safe_float(a.get("VolatilidadFinal"))
            if v == v:
                a["VolatilidadFinal"] = v * m

    elif stype == "multiply_vol_by_country":
        country = scenario["country"]
        m = float(scenario["multiplier"])
        for a in new:
            if str(a.get("Pais", "")).strip() == country:
                v = _safe_float(a.get("VolatilidadFinal"))
                if v == v:
                    a["VolatilidadFinal"] = v * m

    return new


def run_analysis(payload: dict, perfil_declarado: str | None = None,
                 thresholds: dict | None = None,
                 scenarios: dict | None = None) -> dict:
    activos = payload["activos"]
    thresholds = thresholds or DEFAULT_THRESHOLDS
    scenarios = scenarios or DEFAULT_SCENARIOS

    metrics = compute_metrics(activos)
    alerts = generate_alerts(metrics, perfil_declarado, thresholds)
    recs = recommend_rebalancing(activos, metrics, thresholds)

    # escenarios
    scenario_results = []
    for key, sc in scenarios.items():
        shocked_activos = apply_scenario(activos, sc)
        shocked_metrics = compute_metrics(shocked_activos)
        scenario_results.append({
            "id": key,
            "label": sc.get("label", key),
            "delta": {
                "VolPromedioCartera": shocked_metrics["VolPromedioCartera"] - metrics["VolPromedioCartera"],
                "IndiceHerfindahl": shocked_metrics["IndiceHerfindahl"] - metrics["IndiceHerfindahl"],
                "ConcentracionTop3": shocked_metrics["ConcentracionTop3"] - metrics["ConcentracionTop3"],
            },
            "metrics_after": {
                "VolPromedioCartera": shocked_metrics["VolPromedioCartera"],
                "IndiceHerfindahl": shocked_metrics["IndiceHerfindahl"],
                "ConcentracionTop3": shocked_metrics["ConcentracionTop3"],
            }
        })

    result = {
        "metrics": metrics,
        "top_holdings": _top_n_holdings(activos, n=10),
        "alerts": alerts,
        "recommendations": recs,
        "scenarios": scenario_results,
        "perfil_declarado": perfil_declarado,
    }
    return result
