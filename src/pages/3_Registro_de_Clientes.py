import streamlit as st
from src.utils.client_store import list_clients, save_client_meta, ensure_client_dirs, read_history

st.title("AQ Capitals — Registro de clientes")

with st.expander("➕ Crear / actualizar cliente", expanded=True):
    c1, c2 = st.columns(2)
    client_id = c1.text_input("Client ID (único, sin espacios)", placeholder="ej: maria_gomez_001")
    name = c2.text_input("Nombre", placeholder="María Gómez")
    email = st.text_input("Email (opcional)")
    notes = st.text_area("Notas (opcional)", height=80)

    if st.button("Guardar cliente", type="primary", disabled=not client_id or not name):
        save_client_meta(client_id.strip(), name.strip(), email.strip(), notes.strip())
        st.success("Cliente guardado.")
        st.rerun()

st.divider()

clients = list_clients()
if not clients:
    st.info("Todavía no hay clientes cargados.")
    st.stop()

options = {f'{c.get("name","")} — {c.get("client_id","")}': c.get("client_id","") for c in clients}
sel_label = st.selectbox("Seleccioná un cliente", list(options.keys()))
sel_id = options[sel_label]

paths = ensure_client_dirs(sel_id)
st.subheader("Carpeta del cliente")
st.code(paths["base"])

st.subheader("Historial reciente")
hist = read_history(sel_id, limit=50)
if not hist:
    st.caption("Sin historial todavía.")
else:
    for h in reversed(hist[-15:]):
        st.write(f'• {h.get("ts","")} — {h.get("event","")}')

st.caption("Siguiente paso: desde Diagnóstico, guardar Excel/PDF en esta carpeta y registrar eventos.")
