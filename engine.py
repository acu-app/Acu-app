import json
from pathlib import Path
import pandas as pd

def load_config():
    return json.loads(Path("config.json").read_text(encoding="utf-8"))

def read_excel(xlsx_path: Path, cfg: dict):
    df = pd.read_excel(xlsx_path, sheet_name=cfg["sheet_activos"], engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in cfg["required_columns"] if c not in df.columns]
    if missing:
        raise ValueError("Faltan columnas en InputActivos: " + ", ".join(missing))

    for col in ["Peso", "Valor en USD", "ScoreActivoFinal", "VolatilidadFinal", "CountryContextScore"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    wsum = df["Peso"].sum(skipna=True)
    if wsum and abs(wsum - 1.0) > 0.02:
        df["Peso"] = df["Peso"] / wsum

    res = pd.read_excel(xlsx_path, sheet_name=cfg["sheet_resumen"], header=None, engine="openpyxl")
    res = res.iloc[:, :2].dropna(how="all")
    res.columns = ["key", "value"]
    res = res.dropna(subset=["key"])
    res["key"] = res["key"].astype(str).str.strip()
    resumen = dict(zip(res["key"], res["value"]))

    return df, resumen

def weighted_avg(df, value_col):
    return float((df["Peso"] * df[value_col]).sum())

def top_concentration(df, n=3):
    return float(df["Peso"].nlargest(n).sum())

def exposure_by(df, col):
    return df.groupby(col)["Peso"].sum().sort_values(ascending=False).to_dict()
