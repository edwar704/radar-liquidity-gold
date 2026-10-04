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
    st.warning("⚠️ Por favor, despliega el menú lateral izquierdo y haz clic en **1_Login** para iniciar sesión.")
    st.info("Credenciales de prueba:\n- **Admin:** usuario `admin` / clave `admin123`\n- **Invitado:** usuario `invitado1` / clave `gold123`")
else:
    st.success(f"Sesión iniciada como: **{st.session_state['usuario']}** ({st.session_state['rol'].upper()})")
    st.write("Utiliza el menú lateral para navegar entre las páginas disponibles.")
