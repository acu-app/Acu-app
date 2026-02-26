from pathlib import Path
from datetime import datetime

from engine import load_config, read_excel, weighted_avg, top_concentration
from report import save_html


def main():
    cfg = load_config()

    xlsx = input("Ruta del Excel .xlsx (arrastralo acá y Enter): ").strip()

    # limpiar comillas si existen
    if (xlsx.startswith('"') and xlsx.endswith('"')) or (xlsx.startswith("'") and xlsx.endswith("'")):
        xlsx = xlsx[1:-1]

    xlsx = xlsx.replace("\\ ", " ")

    xlsx_path = Path(xlsx)

    nombre = input("Nombre del cliente: ").strip() or "Cliente"

    df, _ = read_excel(xlsx_path, cfg)

    metrics = {
        "score_avg": weighted_avg(df, "ScoreActivoFinal"),
        "top3": top_concentration(df, 3)
    }

    df_top = df.sort_values(by="Peso", ascending=False).head(cfg["top_n"])
    cliente = {"Nombre": nombre}

    out_dir = Path("output") / datetime.now().strftime("%Y-%m-%d")
    out_path = save_html(out_dir, cliente, metrics, df_top)

    print(f"\n✅ Reporte generado: {out_path.resolve()}")


if __name__ == "__main__":
    main()

