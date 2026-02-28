from pathlib import Path
import streamlit as st

def load_css() -> None:
    base_dir = Path(__file__).resolve().parent
    css_path = base_dir / "styles.css"

    if not css_path.exists():
        st.error(f"CSS NOT FOUND: {css_path}")
        return

    css = css_path.read_text(encoding="utf-8")

    # Inyecta el CSS del archivo
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

