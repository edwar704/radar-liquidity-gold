import streamlit as st

st.set_page_config(page_title="Panel Admin - Radar Liquidity", page_icon="⚙️️")

# Control de acceso por rol
if not st.session_state.get("autenticado", False) or st.session_state.get("rol") != "admin":
    st.error("⛔ Acceso denegado. Debe iniciar sesión como Administrador.")
    st.stop()

st.title("⚙️ Panel del Administrador")
st.write("Gestión general del sistema, usuarios y parámetros del bot.")

tab_usr, tab_bot, tab_lic = st.tabs(["Gestión de Usuarios", "Parámetros del Bot", "Licencias"])

with tab_usr:
    st.subheader("Crear / Editar / Suspender Usuarios")
    st.text_input("Nuevo Usuario")
    st.text_input("Contraseña Temporal", type="password")
    st.selectbox("Rol", ["invitado", "admin"])
    if st.button("Guardar Usuario"):
        st.success("Usuario registrado con éxito.")

with tab_bot:
    st.subheader("Configuración Global del Radar Liquidity Gold Bot")
    st.number_input("Período RSI Principal", value=14)
    st.number_input("EMA Rápida", value=8)
    st.number_input("EMA Lenta", value=13)
    if st.button("Actualizar Parámetros del Bot"):
        st.success("Parámetros globales actualizados.")

with tab_lic:
    st.subheader("Control de Suscripciones y Licencias")
    st.write("Aquí puedes activar o revocar accesos a las cuentas conectadas.")
