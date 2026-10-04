import streamlit as st
import random
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(page_title="Radar Liquidity Gold Bot", page_icon="📈", layout="centered")

# Inicializar estado del modo oscuro
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False

def aplicar_estilo(dark_mode=False):
    if dark_mode:
        bg_color = "#0e1117"
        card_bg = "#1e2630"
        text_color = "#ffffff"
        table_bg = "#161b22"
    else:
        bg_color = "#ffffff"
        card_bg = "#f4fbfa"
        text_color = "#333333"
        table_bg = "#f8f9fa"

    estilo_css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap');

    html, body, .stApp {{
        background-color: {bg_color} !important;
        font-family: 'Poppins', sans-serif !important;
    }}
    
    p, span, div, label, h1, h2, h3, h4 {{
        color: {text_color} !important; 
    }}
    
    /* Estilizar botones: Degradado de Azul Claro a Verde */
    div.stButton > button:first-child, div.stFormSubmitButton > button:first-child {{
        background: linear-gradient(135deg, #48cae4 0%, #2a9d8f 100%);
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    div.stButton > button:first-child:hover, div.stFormSubmitButton > button:first-child:hover {{
        background: linear-gradient(135deg, #00b4d8 0%, #21867a 100%);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }}

    /* Personalizar los cuadros de métricas */
    div[data-testid="metric-container"] {{
        background-color: {card_bg} !important;
        border-left: 5px solid #2a9d8f;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}

    /* Tablas adaptables al tema */
    [data-testid="stTable"], [data-testid="stDataFrame"] {{
        background-color: {table_bg} !important;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    </style>
    """
    st.markdown(estilo_css, unsafe_allow_html=True)

aplicar_estilo(st.session_state['dark_mode'])

# ==========================================
# 2. INICIALIZACIÓN DE VARIABLES DE SESIÓN
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'invite_codes' not in st.session_state:
    st.session_state['invite_codes'] = ['GOLD-2026', 'GOLD-DEMO']
if 'last_generated_code' not in st.session_state:
    st.session_state['last_generated_code'] = None

# ==========================================
# 3. BARRA SUPERIOR DE CONTROL (MODO OSCURO)
# ==========================================
col_vacia, col_modo = st.columns([3, 1])
with col_modo:
    modo_oscuro = st.toggle("🌙 Modo Oscuro", value=st.session_state['dark_mode'])
    if modo_oscuro != st.session_state['dark_mode']:
        st.session_state['dark_mode'] = modo_oscuro
        st.rerun()

# ==========================================
# 4. LÓGICA DE LOGIN Y REGISTRO
# ==========================================
def login_screen():
    st.title("Radar Liquidity Gold")
    st.write("Bienvenido. Ingresa tus credenciales para acceder al sistema.")
    
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
                if usuario.strip() != "" and codigo_invitacion.strip() in st.session_state['invite_codes']:
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = 'socio'
                    st.rerun() 
                else:
                    st.error("Código de invitación inválido o usuario vacío.")
                    
    with tab2:
        st.subheader("Panel de Administración")
        with st.form("form_admin"):
            admin_user = st.text_input("Usuario Admin")
            admin_pass = st.text_input("Contraseña", type="password")
            submit_admin = st.form_submit_button("Ingresar como Admin")
            
            if submit_admin:
                if admin_user.strip().lower() == "admin" and admin_pass.strip() == "admin123":
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = 'admin'
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")

# ==========================================
# 5. DASHBOARD DE ADMINISTRADOR
# ==========================================
def admin_dashboard():
    st.title("⚙️ Centro de Control Admin")
    st.write("Monitoreo general y gestión de cuentas del bot.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Códigos Activos", value=len(st.session_state['invite_codes']))
    col2.metric(label="Estado MetaApi", value="Desconectado", delta="Requiere Configuración", delta_color="off")
    col3.metric(label="Socios Conectados", value="0", delta="Sistema en Pausa", delta_color="off")
    
    st.divider()
    
    tab_accesos, tab_api = st.tabs(["🔑 Gestión de Accesos", "🔌 Configuración MetaApi"])
    
    with tab_accesos:
        st.subheader("Control de Invitaciones")
        col_gen, col_lista = st.columns([1, 1.2])
        
        with col_gen:
            st.markdown("#### Crear Código")
            if st.button("➕ Generar Nuevo Código", use_container_width=True):
                nuevo_codigo = f"GOLD-{random.randint(1000, 9999)}"
                st.session_state['invite_codes'].append(nuevo_codigo)
                st.session_state['last_generated_code'] = nuevo_codigo
                st.rerun()
                
            # Muestra el enlace público con la URL de producción
            if st.session_state['last_generated_code']:
                st.success("Enlace listo para compartir:")
                st.code(f"https://radar-liquidity-gold-bot.streamlit.app/?invite={st.session_state['last_generated_code']}")
                
            st.markdown("---")
            st.markdown("#### Eliminar Código")
            if len(st.session_state['invite_codes']) > 0:
                codigo_eliminar = st.selectbox(
                    "Selecciona un código a eliminar:",
                    options=st.session_state['invite_codes']
                )
                if st.button("🗑️ Eliminar Código Seleccionado", use_container_width=True):
                    st.session_state['invite_codes'].remove(codigo_eliminar)
                    if st.session_state['last_generated_code'] == codigo_eliminar:
                        st.session_state['last_generated_code'] = None
                    st.success(f"Código '{codigo_eliminar}' eliminado.")
                    st.rerun()
            else:
                st.info("No hay códigos de invitación para eliminar.")
                
        with col_lista:
            st.markdown("#### Listado de Códigos Activos")
            if len(st.session_state['invite_codes']) > 0:
                df_codigos = pd.DataFrame({
                    "Código de Invitación": st.session_state['invite_codes'],
                    "Estado": ["Activo"] * len(st.session_state['invite_codes'])
                })
                st.dataframe(df_codigos, use_container_width=True, hide_index=True)
            else:
                st.warning("No hay códigos activos en el sistema.")
            
    with tab_api:
        st.subheader("Integración con MetaApi")
        st.write("Ingresa los datos de tu cuenta de MetaApi para sincronizar el bot con MetaTrader 5.")
        with st.form("form_metaapi"):
            st.text_input("Account ID")
            st.text_input("Access Token", type="password")
            st.form_submit_button("Guardar Credenciales")
            
    st.divider()
    
    col_vacia_salir, col_salir = st.columns([3, 1])
    with col_salir:
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['role'] = None
            st.rerun()

# ==========================================
# 6. DASHBOARD DEL SOCIO (EL BOT)
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
    
    col_vacia_salir, col_salir = st.columns([3, 1])
    with col_salir:
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['role'] = None
            st.rerun()

# ==========================================
# 7. CONTROL DE RUTAS PRINCIPAL
# ==========================================
if not st.session_state['logged_in']:
    login_screen()
else:
    if st.session_state['role'] == 'admin':
        admin_dashboard()
    elif st.session_state['role'] == 'socio':
        socio_dashboard()
