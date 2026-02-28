from pathlib import Path
import streamlit as st

def load_css() -> None:
    # path absoluto al directorio donde está este archivo (src/)
    base_dir = Path(__file__).resolve().parent
    css_path = base_dir / "styles.css"

    if not css_path.exists():
        st.warning(f"No se encontró el CSS en: {css_path}")
        return

    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
