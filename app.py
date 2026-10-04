import streamlit as st

# Configuración inicial de la página
st.set_page_config(
    page_title="Radar Liquidity Gold Bot",
    page_icon="🤖",
    layout="wide"
)

# Inicializar variables de sesión para el estado y el tema
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""
if "rol" not in st.session_state:
    st.session_state["rol"] = ""
if "modo_oscuro" not in st.session_state:
    st.session_state["modo_oscuro"] = True

usuarios_db = {
    "admin": {"password": "admin123", "rol": "admin"},
    "invitado1": {"password": "gold123", "rol": "invitado"}
}

# Aplicar estilos CSS dinámicos generales
if st.session_state["modo_oscuro"]:
    st.markdown("""
        <style>
        .stApp {
            background-color: #0e1117;
            color: #ffffff;
        }
        .stTextInput label, .stSelectbox label, .stNumberInput label {
            color: #ffffff !important;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp {
            background-color: #ffffff;
            color: #000000;
        }
        .stTextInput label, .stSelectbox label, .stNumberInput label {
            color: #000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)


# --- FUNCIÓN AISLADA PARA EL PANEL DE ADMINISTRADOR (ESTILO MT5 LIGHT) ---
def render_admin_panel():
    # Inyectamos estilos específicos para darle el toque MT5 Light al panel de admin
    st.markdown("""
        <style>
        .mt5-admin-box {
            background-color: #f4f6f8;
            padding: 20px;
            border-radius: 6px;
            border: 1px solid #dcdcdc;
            color: #111111;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### ⚙️ Panel de Control del Administrador <span style='font-size:14px; color:#555;'>(MT5 Financial Style)</span>", unsafe_allow_html=True)
    
    tab_usuarios, tab_bot, tab_licencias, tab_logs = st.tabs([
        "👥 Gestión de Usuarios", 
        "🤖 Configuración del Bot", 
        "🔑 Licencias y Accesos", 
        "📊 Monitoreo y Logs"
    ])
    
    with tab_usuarios:
        st.markdown('<div class="mt5-admin-box">', unsafe_allow_html=True)
        st.markdown("#### Agregar o Modificar Usuarios")
        nuevo_user = st.text_input("Nombre de Usuario Nuevo", key="admin_new_user")
        nuevo_pass = st.text_input("Contraseña Temporal", type="password", key="admin_new_pass")
        rol_select = st.selectbox("Rol", ["admin", "invitado"], key="admin_rol_select")
        if st.button("Registrar Usuario", key="admin_btn_reg"):
            st.success(f"¡Usuario {nuevo_user} registrado con éxito!")
        st.markdown('</div>', unsafe_allow_html=True)
            
    with tab_bot:
        st.markdown('<div class="mt5-admin-box">', unsafe_allow_html=True)
        st.markdown("#### Parámetros Globales del Bot")
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("RSI Período Global", value=14, key="admin_rsi")
            st.number_input("EMA Rápida Global", value=8, key="admin_ema")
        with col2:
            st.number_input("Límite de Riesgo Diario (%)", value=2.0, key="admin_risk")
        if st.button("Guardar Parámetros Globales", key="admin_btn_params"):
            st.success("Parámetros actualizados para todos los usuarios.")
        st.markdown('</div>', unsafe_allow_html=True)
            
    with tab_licencias:
        st.markdown('<div class="mt5-admin-box">', unsafe_allow_html=True)
        st.markdown("#### Control de Suscripciones Activas")
        st.info("Aquí puedes activar o suspender licencias de MetaTrader 5.")
        st.metric(label="Licencias Activas", value="12", delta="+2 este mes")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with tab_logs:
        st.markdown('<div class="mt5-admin-box">', unsafe_allow_html=True)
        st.markdown("#### Registro de Actividad del Sistema")
        st.code("""
[INFO] 2026-10-04 07:00:00 - Sistema iniciado correctamente.
[INFO] 2026-10-04 07:05:12 - Usuario 'admin' inició sesión.
[SUCCESS] 2026-10-04 07:10:30 - Parámetros del bot sincronizados.
        """, language="text")
        st.markdown('</div>', unsafe_allow_html=True)


# --- PANTALLA DE LOGIN CENTRADA Y COMPACTA ---
if not st.session_state["autenticado"]:
    col_space, col_btn = st.columns([5, 1])
    with col_btn:
        icono_modo = "☀ Claro" if st.session_state["modo_oscuro"] else "🌙 Oscuro"
        if st.button(icono_modo):
            st.session_state["modo_oscuro"] = not st.session_state["modo_oscuro"]
            st.rerun()

    col_left, col_center, col_right = st.columns([1.2, 1, 1.2])
    
    with col_center:
        st.markdown("<h2 style='text-align: center;'>Bienvenidos a Radar liquidity Gold Bot</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Iniciar Sesión</p>", unsafe_allow_html=True)
        
        usuario_input = st.text_input("Usuario", key="login_user")
        password_input = st.text_input("Contraseña", type="password", key="login_pass")
        
        st.write("") 
        if st.button("Ingresar", use_container_width=True, key="login_btn"):
            if usuario_input in usuarios_db and usuarios_db[usuario_input]["password"] == password_input:
                st.session_state["autenticado"] = True
                st.session_state["usuario"] = usuario_input
                st.session_state["rol"] = usuarios_db[usuario_input]["rol"]
                st.success("¡Ingreso exitoso!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

# --- PÁGINAS SEGÚN EL ROL (Una vez logueado) ---
else:
    col_title, col_theme, col_logout = st.columns([3, 1, 1])
    
    with col_title:
        st.title("Bienvenidos a Radar liquidity Gold Bot")
        st.caption(f"Sesión activa: **{st.session_state['usuario']}** ({st.session_state['rol'].upper()})")
        
    with col_theme:
        st.write("") 
        icono_modo = "☀ Claro" if st.session_state["modo_oscuro"] else "🌙 Oscuro"
        if st.button(icono_modo):
            st.session_state["modo_oscuro"] = not st.session_state["modo_oscuro"]
            st.rerun()
            
    with col_logout:
        st.write("")
        if st.button("Cerrar Sesión", use_container_width=True, key="logout_btn"):
            st.session_state["autenticado"] = False
            st.session_state["usuario"] = ""
            st.session_state["rol"] = ""
            st.rerun()
            
    st.divider()

    # Vista para Administrador (Llama a nuestra función modular aislada con estilo MT5)
    if st.session_state["rol"] == "admin":
        render_admin_panel()

    # Vista para Invitado (Intacta)
    elif st.session_state["rol"] == "invitado":
        st.subheader("📊 Panel del Invitado & Monitoreo del Bot")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🔌 Conexión MT5")
            st.text_input("Cuenta MT5", key="guest_acc")
            st.text_input("Contraseña MT5", type="password", key="guest_pass")
            st.button("Conectar MT5", key="guest_btn_conn")
            
        with col2:
            st.markdown("### 🛡 Gestión de Riesgo")
            st.number_input("Lotaje", value=0.1, key="guest_lot")
            st.number_input("Stop Loss (Pips)", value=50, key="guest_sl")
            st.button("Guardar Riesgo", key="guest_btn_risk")
            
        st.divider()
        st.subheader("🚨 Control de Emergencia")
        if st.button("🔴 DETENER OPERACIONES MT5", type="primary", key="guest_emergency"):
            st.error("¡Operaciones pausadas de emergencia!")
