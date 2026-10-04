import streamlit as st

# Configuración inicial de la página principal
st.set_page_config(
    page_title="Radar Liquidity Gold Bot",
    page_icon="🤖",
    layout="wide"
)

# Control de sesión inicial
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""
if "rol" not in st.session_state:
    st.session_state["rol"] = ""

st.title("🤖 Radar Liquidity Gold Bot")
st.write("Bienvenido al sistema automatizado de trading y gestión de liquidez.")

if not st.session_state["autenticado"]:
    st.warning("⚠️️ Por favor, inicia sesión para acceder a las funciones del sistema.")
    st.info("Credenciales de prueba:\n- **Admin:** usuario `admin` / clave `admin123`\n- **Invitado:** usuario `invitado1` / clave `gold123`")
else:
    st.success(f"Sesión iniciada como: **{st.session_state['usuario']}** ({st.session_state['rol'].upper()})")

st.divider()

# Botones de navegación directos en pantalla
st.subheader("📌 Navegación del Sistema")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔐 Ir al Login"):
        st.switch_page("pages/1_Login.py")

with col2:
    if st.button("⚙️ Panel Admin"):
        st.switch_page("pages/2_Panel_Admin.py")

with col3:
    if st.button("📊 Panel Invitado"):
        st.switch_page("pages/3_Panel_Invitado.py")

with col4:
    if st.button("🤖 Monitoreo Bot"):
        st.switch_page("pages/4_Bot.py")
