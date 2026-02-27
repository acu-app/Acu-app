import streamlit as st
from pathlib import Path

def load_css():
    css_path = Path(__file__).parent / "styles.css"   # src/styles.css
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)
