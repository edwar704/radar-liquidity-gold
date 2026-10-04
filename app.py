import streamlit as st
import random
import time
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(page_title="Radar Liquidity Gold Bot", page_icon="🥇", layout="centered")

def aplicar_estilo_amigable():
    estilo_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap');

    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Poppins', sans-serif !important;
    }
    
    p, span, div {
        color: #333333; 
    }
    
    /* Estilizar botones para dar más confianza (bordes redondeados y color azul profesional) */
    div.stButton > button:first-child {
        background-color: #0056b3;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #004494;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
    """
    st.markdown(estilo_css, unsafe_allow_html=True)

aplicar_estilo_amigable()

# ==========================================
# 2. INICIALIZACIÓN DE VARIABLES DE SESIÓN
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'invite_codes' not in st.session_state:
    st.session_state['invite_codes'] = ['GOLD-2026', 'GOLD-DEMO'] # Códigos por defecto

# ==========================================
# 3. LÓGICA DE LOGIN Y REGISTRO
# ==========================================
def login_screen():
    st.title("🥇 Radar Liquidity Gold")
    st.write("Bienvenido. Ingresa tus credenciales para acceder al sistema.")
    
    # Capturar código de invitación de la URL si existe
    params = st.query_params
    codigo_url = params.get("invite", "")
    
    tab1, tab2 = st.tabs(["Acceso Socios", "Acceso Administrador"])
    
    with tab1:
        st.subheader("Acceso para Socios")
        usuario = st.text_input("Usuario", key="socio_user")
        # Si hay código en la URL, se autocompleta
        codigo_invitacion = st.text_input("Código de Invitación", value=codigo_url, key="socio_code")
        
        if st.button("Ingresar como Socio"):
            if usuario and codigo_invitacion in st.session_state['invite_codes']:
                st.session_state['logged_in'] = True
                st.session_state['role'] = 'socio'
                st.success(f"Bienvenido, {usuario}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Código de invitación inválido o usuario vacío.")
                
    with tab2:
        st.subheader("Panel de Administración")
        admin_user = st.text_input("Usuario Admin", key="admin_user")
        admin_pass = st.text_input("Contraseña", type="password", key="admin_pass")
        
        if st.button("Ingresar como Admin"):
            if admin_user == "admin" and admin_pass == "admin123": # Cambia esta contraseña en producción
                st.session_state['logged_in'] = True
                st.session_state['role'] = 'admin'
                st.success("Acceso de administrador concedido.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Credenciales de administrador incorrectas.")

# ==========================================
# 4. DASHBOARD DE ADMINISTRADOR
# ==========================================
def admin_dashboard():
    st.title("⚙️ Panel de Control Admin")
    st.write("Gestión de códigos y cuentas MetaApi conectadas.")
    
    if st.button("Generar Nuevo Código de Invitación"):
        nuevo_codigo = f"GOLD-{random.randint(1000, 9999)}"
        st.session_state['invite_codes'].append(nuevo_codigo)
        st.success(f"Código generado: {nuevo_codigo}")
        # Muestra el link para copiar
        st.code(f"http://localhost:8501/?invite={nuevo_codigo}")
        
    st.subheader("Códigos Activos")
    st.write(st.session_state['invite_codes'])
    
    st.divider()
    if st.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()

# ==========================================
# 5. DASHBOARD DEL SOCIO (EL BOT)
# ==========================================
def socio_dashboard():
    st.title("📊 Radar Liquidity Gold Bot")
    st.write("Monitoreo institucional XAU/USD en tiempo real.")
    
    # Simulador de precios Bid/Ask
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Precio BID", value="2045.50", delta="-1.2")
    with col2:
        st.metric(label="Precio ASK", value="2045.80", delta="-1.2")
        
    st.divider()
    
    # Simulador de Zonas de Liquidez
    st.subheader("Zonas de Liquidez Detectadas")
    datos_liquidez = pd.DataFrame({
        'Zona': ['Buy Stops (Resistencia)', 'Sell Stops (Soporte)'],
        'Precio Nivel': ['2052.00', '2038.50'],
        'Volumen Estimado': ['Alto', 'Medio'],
        'Estado': ['Esperando toma de liquidez', 'Monitoreando']
    })
    st.table(datos_liquidez)
    
    st.info("💡 El bot está analizando el mercado a través de MetaApi. Esperando el próximo Order Block para ejecutar entrada.")
    
    st.divider()
    if st.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.rerun()

# ==========================================
# 6. CONTROL DE RUTAS PRINCIPAL
# ==========================================
if not st.session_state['logged_in']:
    login_screen()
else:
    if st.session_state['role'] == 'admin':
        admin_dashboard()
    elif st.session_state['role'] == 'socio':
        socio_dashboard()
