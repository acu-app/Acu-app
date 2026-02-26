import os
import json
from datetime import datetime
import pandas as pd


REQUIRED_COLUMNS = [
    "Activo",
    "Tipo",
    "Pais",
    "Moneda",
    "Valor en USD",
    "Peso",
    "VolatilidadFinal",
    "ScoreActivoFinal",
]


def read_portfolio_excel(xlsx_path: str) -> dict:
    """
    Lee el Excel del cliente y devuelve un diccionario estructurado.
    """

    if not os.path.exists(xlsx_path):
        raise FileNotFoundError(f"No se encontró el archivo: {xlsx_path}")

    # Leer hojas
    xl = pd.ExcelFile(xlsx_path)

    if "InputActivos" not in xl.sheet_names:
        raise ValueError("El Excel no tiene la hoja 'InputActivos'.")

    df = xl.parse("InputActivos")

    # Limpiar filas vacías
    df = df.dropna(how="all")

    # Validar columnas obligatorias
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Falta la columna obligatoria: {col}")

    # Convertir columnas numéricas
    numeric_cols = ["Valor en USD", "Peso", "VolatilidadFinal", "ScoreActivoFinal"]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Eliminar filas con valores inválidos
    df = df.dropna(subset=numeric_cols)

    # Validar suma de pesos
    peso_total = df["Peso"].sum()

    if peso_total > 1.5:  # probablemente suma 100
        df["Peso"] = df["Peso"] / 100
        peso_total = df["Peso"].sum()

    if not 0.99 <= peso_total <= 1.01:
        print(f"⚠️ Advertencia: los pesos suman {peso_total:.4f} (debería ser 1).")

    # Convertir a lista de diccionarios
    activos = df.to_dict(orient="records")

    payload = {
        "metadata": {
            "source_file": os.path.basename(xlsx_path),
            "generated_at": datetime.now().isoformat(),
        },
        "activos": activos,
    }

    return payload


def write_analysis_json(payload: dict, output_base: str = "output") -> str:
    """
    Guarda el JSON en output/YYYY-MM-DD/analysis.json
    """

    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(output_base, today)

    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "analysis.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return output_path
