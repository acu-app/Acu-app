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

    # Badge de debug (si lo ves, el CSS se está ejecutando)
    st.markdown("""
        <style>
          .acu-debug-badge{
            position: fixed; top: 14px; right: 14px; z-index: 99999;
            background:#111827; color:white; padding:6px 10px;
            border-radius:10px; font-size:12px; font-weight:700;
            box-shadow: 0 4px 12px rgba(0,0,0,.15);
          }
        </style>
        <div class="acu-debug-badge">ACU CSS ON</div>
    """, unsafe_allow_html=True)
    st.sidebar.caption(f"CSS PATH: {css_path}")
