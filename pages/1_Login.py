import streamlit as st

st.set_page_config(page_title="Login - Radar Liquidity", page_icon="🔐")

st.title("🔐 Iniciar Sesión")

# Base de datos simulada en memoria
if "usuarios_db" not in st.session_state:
    st.session_state["usuarios_db"] = {
        "admin": {"password": "admin123", "rol": "admin"},
        "invitado1": {"password": "gold123", "rol": "invitado"}
    }

if st.session_state.get("autenticado", False):
    st.success(f"Ya has iniciado sesión como **{st.session_state['usuario']}** ({st.session_state['rol'].upper()}).")
    if st.button("Cerrar Sesión"):
        st.session_state["autenticado"] = False
        st.session_state["usuario"] = ""
        st.session_state["rol"] = ""
        st.rerun()
else:
    # Solo los dos recuadros solicitados
    usuario_input = st.text_input("Usuario")
    password_input = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        db = st.session_state["usuarios_db"]
        if usuario_input in db and db[usuario_input]["password"] == password_input:
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = usuario_input
            st.session_state["rol"] = db[usuario_input]["rol"]
            st.success("¡Ingreso exitoso!")
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
