from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

from engine import load_config, read_excel, weighted_avg, top_concentration
from report import save_html

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AcuScore")
        self.geometry("500x250")
        self.cfg = load_config()
        self.xlsx_path = None

        tk.Label(self, text="Nombre Cliente").pack()
        self.e_nombre = tk.Entry(self)
        self.e_nombre.pack()

        tk.Button(self, text="Seleccionar Excel", command=self.pick_file).pack(pady=10)
        tk.Button(self, text="Generar Reporte", command=self.run).pack()

    def pick_file(self):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if p:
            self.xlsx_path = Path(p)

    def run(self):
        try:
            if not self.xlsx_path:
                messagebox.showerror("Error", "Seleccioná un Excel")
                return

            df, _ = read_excel(self.xlsx_path, self.cfg)
            metrics = {
                "score_avg": weighted_avg(df, "ScoreActivoFinal"),
                "top3": top_concentration(df, 3)
            }

            df_top = df.sort_values(by="Peso", ascending=False).head(10)
            cliente = {"Nombre": self.e_nombre.get() or "Cliente"}

            out_dir = Path("output") / datetime.now().strftime("%Y-%m-%d")
            out_path = save_html(out_dir, cliente, metrics, df_top)

            messagebox.showinfo("OK", f"Reporte generado:\n{out_path}")

        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    App().mainloop()
