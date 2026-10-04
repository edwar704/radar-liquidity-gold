import streamlit as st

st.set_page_config(
    page_title="Radar Liquidity Gold Bot",
    page_icon="🤖",
    layout="wide"
)

# Inicializar variables de sesión
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""
if "rol" not in st.session_state:
    st.session_state["rol"] = ""

usuarios_db = {
    "admin": {"password": "admin123", "rol": "admin"},
    "invitado1": {"password": "gold123", "rol": "invitado"}
}

# --- PANTALLA DE LOGIN CENTRADA Y COMPACTA ---
if not st.session_state["autenticado"]:
    # Creamos columnas para dejar espacios a los lados y centrar el cuadro
    col_left, col_center, col_right = st.columns([1.2, 1, 1.2])
    
    with col_center:
        st.markdown("<h2 style='text-align: center;'>🤖 Radar Liquidity</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Iniciar Sesión</p>", unsafe_allow_html=True)
        
        usuario_input = st.text_input("Usuario")
        password_input = st.text_input("Contraseña", type="password")
        
        st.write("") # Espaciado
        if st.button("Ingresar", use_container_width=True):
            if usuario_input in usuarios_db and usuarios_db[usuario_input]["password"] == password_input:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario_input
                st.session_state["rol"] = usuarios_db[usuario_input]["rol"]
                st.success("¡Ingreso exitoso!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
                
        st.info("Prueba:\n- `admin` / `admin123`\n- `invitado1` / `gold123`")

# --- PANTALLAS SEGÚN EL ROL (Una vez logueado) ---
else:
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title(f"🤖 Radar Liquidity Gold Bot - Panel de {st.session_state['rol'].capitalize()}")
    with col_logout:
        if st.button("Cerrar Sesión"):
            st.session_state["autenticado"] = False
            st.session_state["usuario"] = ""
            st.session_state["rol"] = ""
            st.rerun()
            
    st.divider()

    # Vista para Administrador
    if st.session_state["rol"] == "admin":
        st.subheader("⚙️ Panel del Administrador")
        tab_usr, tab_bot, tab_lic = st.tabs(["Gestión de Usuarios", "Parámetros del Bot", "Licencias"])
        
        with tab_usr:
            st.text_input("Nuevo Usuario")
            st.text_input("Contraseña Temporal", type="password")
            if st.button("Guardar Usuario"):
                st.success("Usuario registrado.")
                
        with tab_bot:
            st.number_input("Período RSI Principal", value=14)
            st.number_input("EMA Rápida", value=8)
            if st.button("Actualizar Parámetros"):
                st.success("Parámetros globales actualizados.")
                
        with tab_lic:
            st.write("Control de suscripciones activas.")

    # Vista para Invitado
    elif st.session_state["rol"] == "invitado":
        st.subheader("📊 Panel del Invitado & Monitoreo del Bot")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🔌 Conexión MT5")
            st.text_input("Cuenta MT5")
            st.text_input("Contraseña MT5", type="password")
            st.button("Conectar MT5")
            
        with col2:
            st.markdown("### 🛡️ Gestión de Riesgo")
            st.number_input("Lotaje", value=0.1)
            st.number_input("Stop Loss (Pips)", value=50)
            st.button("Guardar Riesgo")
            
        st.divider()
        st.subheader("🚨 Control de Emergencia")
        if st.button("🔴 DETENER OPERACIONES MT5", type="primary"):
            st.error("¡Operaciones pausadas de emergencia!")
