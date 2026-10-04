import streamlit as st
import random
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(page_title="Radar Liquidity Gold Bot", page_icon="📈", layout="centered")

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
    
    /* Estilizar botones: Degradado de Azul Claro a Verde */
    div.stButton > button:first-child, div.stFormSubmitButton > button:first-child {
        background: linear-gradient(135deg, #48cae4 0%, #2a9d8f 100%);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    div.stButton > button:first-child:hover, div.stFormSubmitButton > button:first-child:hover {
        background: linear-gradient(135deg, #00b4d8 0%, #21867a 100%);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }

    /* Personalizar los cuadros de métricas (Precios Bid/Ask) */
    div[data-testid="metric-container"] {
        background-color: #f4fbfa;
        border-left: 5px solid #2a9d8f;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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
    st.session_state['invite_codes'] = ['GOLD-2026', 'GOLD-DEMO']

# ==========================================
# 3. LÓGICA DE LOGIN Y REGISTRO (CON st.form MEJORADO)
# ==========================================
def login_screen():
    st.title("Radar Liquidity Gold")
    st.write("Bienvenido. Ingresa tus credenciales para acceder al sistema.")
    
    # Manejo seguro de parámetros de URL 
    try:
        codigo_url = st.query_params.get("invite", "")
    except AttributeError:
        codigo_url = ""
    
    tab1, tab2 = st.tabs(["Acceso Socios", "Acceso Administrador"])
    
    with tab1:
        st.subheader("Acceso para Socios")
        with st.form("form_socio"):
            usuario = st.text_input("Usuario")
            codigo_invitacion = st.text_input("Código de Invitación", value=codigo_url)
            submit_socio = st.form_submit_button("Ingresar como Socio")
            
            if submit_socio:
                # Usamos .strip() para limpiar espacios invisibles
                if usuario.strip() != "" and codigo_invitacion.strip() in st.session_state['invite_codes']:
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = 'socio'
                    st.rerun() 
                else:
                    st.error("Código de invitación inválido o usuario vacío. Verifica que no haya espacios extra.")
                    
    with tab2:
        st.subheader("Panel de Administración")
        with st.form("form_admin"):
            admin_user = st.text_input("Usuario Admin")
            admin_pass = st.text_input("Contraseña", type="password")
            submit_admin = st.form_submit_button("Ingresar como Admin")
            
            if submit_admin:
                # Limpiamos espacios con .strip() y convertimos el usuario a minúsculas (.lower())
                # para que "Admin", "admin ", o " ADMIN " funcionen igual.
                if admin_user.strip().lower() == "admin" and admin_pass.strip() == "admin123":
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = 'admin'
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifica que no tengas espacios en blanco al final.")

# ==========================================
# 4. DASHBOARD DE ADMINISTRADOR
# ==========================================
def admin_dashboard():
    st.title("Panel de Control Admin")
    st.write("Gestión de códigos y cuentas MetaApi conectadas.")
    
    if st.button("Generar Nuevo Código de Invitación"):
        nuevo_codigo = f"GOLD-{random.randint(1000, 9999)}"
        st.session_state['invite_codes'].append(nuevo_codigo)
        st.success(f"Código generado: {nuevo_codigo}")
        st.code(f"http://localhost:8501/?invite={nuevo_codigo}")
        
    st.subheader("Códigos Activos")
    st.write(st.session_state['invite_codes'])
    
    st.divider()
    if st.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.session_state['role'] = None
        st.rerun()

# ==========================================
# 5. DASHBOARD DEL SOCIO (EL BOT)
# ==========================================
def socio_dashboard():
    st.title("Radar Liquidity Gold Bot")
    st.write("Monitoreo institucional XAU/USD en tiempo real.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Precio BID", value="2045.50", delta="-1.2")
    with col2:
        st.metric(label="Precio ASK", value="2045.80", delta="-1.2")
        
    st.divider()
    
    st.subheader("Zonas de Liquidez Detectadas")
    datos_liquidez = pd.DataFrame({
        'Zona': ['Buy Stops (Resistencia)', 'Sell Stops (Soporte)'],
        'Precio Nivel': ['2052.00', '2038.50'],
        'Volumen Estimado': ['Alto', 'Medio'],
        'Estado': ['Esperando toma de liquidez', 'Monitoreando']
    })
    st.table(datos_liquidez)
    
    st.info("El bot está analizando el mercado a través de MetaApi. Esperando el próximo Order Block para ejecutar entrada.")
    
    st.divider()
    if st.button("Cerrar Sesión"):
        st.session_state['logged_in'] = False
        st.session_state['role'] = None
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
