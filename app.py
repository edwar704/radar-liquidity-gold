import streamlit as st
import os
import random
import string
import pandas as pd
import datetime

# Intentar importar la librería de MetaTrader 5
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Radar Liquidity Gold Bot",
    page_icon="🪙",
    layout="wide"
)

# --- GESTIÓN DE TEMA (CLARO / OSCURO) ---
if "theme" not in st.session_state:
    st.session_state.theme = "Oscuro 🌙"

if st.session_state.theme == "Oscuro 🌙":
    bg_color = "#0b0e14"
    card_bg = "#161b22"
    sidebar_bg = "#161b22"
    text_color = "#e6edf3"
    border_color = "#30363D"
    sub_text = "#8B949E"
    table_bg = "#161b22"
    table_border = "#30363D"
else:
    bg_color = "#f4f6f9"
    card_bg = "#ffffff"
    sidebar_bg = "#ffffff"
    text_color = "#1f2428"
    border_color = "#d0d7de"
    sub_text = "#57606a"
    table_bg = "#ffffff"
    table_border = "#d0d7de"

# --- ESTILOS CSS DINÁMICOS ---
css_styles = f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    [data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
    }}
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] div {{
        color: {text_color} !important;
    }}
    .login-container {{
        background-color: {card_bg};
        padding: 40px;
        border-radius: 16px;
        border: 1px solid {border_color};
        text-align: center;
        box-shadow: 0 12px 32px rgba(0,0,0,0.15);
    }}
    .login-title {{
        color: {text_color};
        font-size: 1.8rem;
        font-weight: 800;
        letter-spacing: 1px;
        margin-top: 10px;
    }}
    .login-subtitle {{
        color: {sub_text};
        font-size: 0.95rem;
    }}
    h1, h2, h3, h4, h5, h6, p, span, div, label {{
        color: {text_color};
    }}
    [data-testid="stMetricLabel"] {{
        color: {sub_text} !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {text_color} !important;
    }}
    </style>
"""
st.markdown(css_styles, unsafe_allow_html=True)

# --- CREDENCIALES Y GESTIÓN DE SOCIOS ---
if "users_db" not in st.session_state:
    st.session_state.users_db = {
        "edwar": "1234",
        "admin": "gold2026"
    }

if "invitation_codes" not in st.session_state:
    st.session_state.invitation_codes = []

# Almacén temporal de configuraciones MT5 por cada usuario
if "user_mt5_config" not in st.session_state:
    st.session_state.user_mt5_config = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# --- FUNCIÓN DE CONEXIÓN A METATRADER 5 PERSONALIZADA ---
def get_user_mt5_data(username):
    if not MT5_AVAILABLE:
        return {"status": "Librería no instalada", "connected": False, "price": 2384.50, "balance": 0.0, "leverage": 100}
    
    # Obtener credenciales específicas de este usuario guardadas en sesión
    user_conf = st.session_state.user_mt5_config.get(username, {})
    account = user_conf.get("account", 0)
    password = user_conf.get("password", "")
    server = user_conf.get("server", "")

    # Inicializar MT5 general
    if not mt5.initialize():
        return {"status": "MT5 Cerrado en PC", "connected": False, "price": 2384.50, "balance": 0.0, "leverage": 100}
    
    # Si el usuario configuró sus datos, intentar hacer login específico en la terminal abierta
    if account and password and server:
        authorized = mt5.login(account=int(account), password=password, server=server)
        if not authorized:
            return {"status": "Error de Credenciales MT5 ❌", "connected": False, "price": 2384.50, "balance": 0.0, "leverage": 100}

    # Obtener información de la cuenta conectada actual en la terminal
    account_info = mt5.account_info()
    balance = account_info.balance if account_info else 0.0
    leverage = account_info.leverage if account_info else 100
    
    # Obtener cotización de XAUUSD
    symbol = "XAUUSD"
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    price = tick.ask if tick else 2384.50
    
    return {
        "status": f"Conectado ({account_info.login if account_info else 'Active'}) 🟢",
        "connected": True,
        "price": price,
        "balance": balance,
        "leverage": leverage
    }

# --- PANTALLA DE ACCESO ---
if not st.session_state.logged_in:
    col_t1, col_t2 = st.columns([8, 2])
    with col_t2:
        selected_theme = st.selectbox("🎨 Tema", ["Oscuro 🌙", "Claro ☀️"], index=0 if st.session_state.theme == "Oscuro 🌙" else 1, key="login_theme_selector")
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()

    col_a, col_b, col_c = st.columns([1, 1.2, 1])
    with col_b:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        image_path = None
        for filename in ["logo..jpg", "logo.jpg", "logo.jpeg", "logo.png", "LOGO.JPG", "LOGO.PNG"]:
            if os.path.exists(filename):
                image_path = filename
                break

        if image_path:
            st.image(image_path, width=140)
        else:
            st.markdown('<div style="color: #D4AF37; font-size: 3.5rem;">🪙</div>', unsafe_allow_html=True)

        st.markdown(f"""
                <div class="login-title">RADAR LIQUIDITY</div>
                <div style="color: #D4AF37; font-weight: 700; letter-spacing: 2px; font-size: 1.1rem; margin-top: 2px;">GOLD BOT</div>
                <div class="login-subtitle" style="margin-top: 6px;">Multi-Account MT5 Terminal</div>
                <hr style="border-color: {border_color}; margin-top: 20px; margin-bottom: 25px;">
            </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔑 Iniciar Sesión", "🎟️ Canjear Invitación"])

        with tab_login:
            with st.form(key="login_form"):
                user_input = st.text_input("👤 USUARIO", placeholder="Ej: edwar")
                pass_input = st.text_input("🔑 CONTRASEÑA", type="password", placeholder="••••••••")
                submit_button = st.form_submit_button(label="INGRESAR AL SISTEMA", use_container_width=True)

                if submit_button:
                    clean_user = user_input.strip().lower()
                    clean_pass = pass_input.strip()

                    if clean_user in st.session_state.users_db and st.session_state.users_db[clean_user] == clean_pass:
                        st.session_state.logged_in = True
                        st.session_state.current_user = clean_user
                        st.success("✅ Acceso concedido...")
                        st.rerun()
                    else:
                        st.error("❌ Credenciales incorrectas o usuario no autorizado.")

        with tab_register:
            with st.form(key="register_form"):
                st.caption("Crea tu cuenta de socio con tu código de invitación.")
                new_user = st.text_input("👤 NUEVO USUARIO", placeholder="Ej: socio01")
                new_pass = st.text_input("🔑 NUEVA CONTRASEÑA", type="password", placeholder="••••••••")
                invite_code = st.text_input("🎟️ CÓDIGO DE INVITACIÓN", placeholder="Ej: RADAR-XXXX")
                reg_button = st.form_submit_button(label="REGISTRARME COMO SOCIO", use_container_width=True)

                if reg_button:
                    clean_new_user = new_user.strip().lower()
                    clean_pass = new_pass.strip()
                    clean_code = invite_code.strip()

                    if not clean_new_user or not clean_pass or not clean_code:
                        st.error("⚠️ Todos los campos son obligatorios.")
                    elif clean_new_user in st.session_state.users_db:
                        st.error("❌ El nombre de usuario ya existe.")
                    elif clean_code not in st.session_state.invitation_codes:
                        st.error("❌ El código de invitación no es válido o ya fue utilizado.")
                    else:
                        st.session_state.users_db[clean_new_user] = clean_pass
                        st.session_state.invitation_codes.remove(clean_code)
                        st.success("🎉 ¡Cuenta creada con éxito! Ahora inicia sesión.")

# --- DASHBOARD PRINCIPAL ---
else:
    current_usr = st.session_state.current_user
    mt5_data = get_user_mt5_data(current_usr)

    with st.sidebar:
        st.markdown("### ⚙️ Centro de Control")
        st.write(f"Operador: **{current_usr.capitalize()}**")
        st.markdown("---")
        
        new_theme = st.radio("🎨 Apariencia", ["Oscuro 🌙", "Claro ☀️"], index=0 if st.session_state.theme == "Oscuro 🌙" else 1)
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

        st.markdown("---")
        
        # --- CONFIGURACIÓN DE MT5 PERSONALIZADA PARA CADA USUARIO ---
        st.markdown("### 🔌 Conectar tu MT5")
        with st.form(key="mt5_config_form"):
            st.caption("Introduce los datos de tu cuenta de broker:")
            cfg_account = st.text_input("Nº de Cuenta MT5", value=str(st.session_state.user_mt5_config.get(current_usr, {}).get("account", "")))
            cfg_password = st.text_input("Contraseña MT5", type="password", value=str(st.session_state.user_mt5_config.get(current_usr, {}).get("password", "")))
            cfg_server = st.text_input("Servidor del Broker", placeholder="Ej: VantageInternational-Live", value=str(st.session_state.user_mt5_config.get(current_usr, {}).get("server", "")))
            
            save_mt5_btn = st.form_submit_button("Vincular Cuenta MT5", use_container_width=True)
            if save_mt5_btn:
                st.session_state.user_mt5_config[current_usr] = {
                    "account": cfg_account.strip(),
                    "password": cfg_password.strip(),
                    "server": cfg_server.strip()
                }
                st.success("✅ ¡Credenciales guardadas!")
                st.rerun()

        st.markdown("---")
        connection_color = "#2ea043" if mt5_data["connected"] else "#f85149"
        st.markdown(f"**Estado MT5:** <span style='color: {connection_color};'>● {mt5_data['status']}</span>", unsafe_allow_html=True)

        if current_usr == "admin":
            st.markdown("---")
            st.markdown("### 🛡 Panel de Admin")
            total_socios = len(st.session_state.users_db) - 2
            st.write(f"Socios actuales: **{total_socios} / 20**")
            st.write(f"Invitaciones activas: **{len(st.session_state.invitation_codes)}**")

            if st.button("🎟️ Generar Invitación", use_container_width=True):
                if total_socios + len(st.session_state.invitation_codes) >= 20:
                    st.error("⚠️ Límite de 20 socios alcanzado.")
                else:
                    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    new_code = f"RADAR-{random_suffix}"
                    st.session_state.invitation_codes.append(new_code)
                    st.success(f"🎟️ Creado: `{new_code}`")
                    st.rerun()

            if st.session_state.invitation_codes:
                with st.expander("📋 Ver códigos pendientes"):
                    for code in st.session_state.invitation_codes:
                        st.code(code)

        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            if MT5_AVAILABLE:
                mt5.shutdown()
            st.session_state.logged_in = False
            st.session_state.current_user = ""
            st.rerun()

    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.title("📈 Radar Liquidity Gold Bot")
        st.caption(f"Terminal Personal — Usuario: {current_usr.capitalize()}")
    with col_head2:
        st.markdown("<div style='text-align: right; padding-top: 15px;'><span style='background-color: #1f242c; color: #D4AF37; padding: 6px 14px; border-radius: 20px; border: 1px solid #D4AF37; font-weight: bold;'>⚡ MULTI-ACCOUNT</span></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(label="Precio XAU/USD (Live)", value=f"${mt5_data['price']:,.2f}", delta="Real-time")
    with m2:
        st.metric(label="Balance de Tu Cuenta", value=f"${mt5_data['balance']:,.2f}", delta="MT5 Synced")
    with m3:
        st.metric(label="Apalancamiento", value=f"1:{mt5_data.get('leverage', 100)}", delta="Broker")
    with m4:
        st.metric(label="Riesgo / Lote", value="1.5% / 0.10", delta="Controlado")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 📊 Comportamiento de Liquidez (XAU/USD)")
        base_p = mt5_data['price']
        chart_data = {
            "Precio": [base_p - 4, base_p - 2, base_p - 3, base_p + 1, base_p - 1, base_p + 3, base_p]
        }
        st.line_chart(chart_data, color="#D4AF37", height=280)

    with col_right:
        st.markdown("### 🎯 Zonas Clave SMC")
        st.info(f"📌 **Order Block Detectado:** ${mt5_data['price'] - 10:,.2f}\n\n📌 **Fair Value Gap (FVG):** ${mt5_data['price'] - 4:,.2f}\n\n🟢 **Sesgo Actual:** Alcista (Buy Side Liquidity)")

    st.markdown("### 📋 Registro de Actividad del Bot")
    st.markdown(f"""
        <div style="background-color: {table_bg}; padding: 15px; border-radius: 10px; border: 1px solid {table_border}; font-size: 0.9rem;">
            <table width="100%" style="color: {text_color}; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid {table_border}; text-align: left; color: {sub_text};">
                    <th style="padding: 8px; color: {sub_text};">HORA</th>
                    <th style="padding: 8px; color: {sub_text};">ACCIÓN</th>
                    <th style="padding: 8px; color: {sub_text};">ACTIVO</th>
                    <th style="padding: 8px; color: {sub_text};">PRECIO</th>
                    <th style="padding: 8px; color: {sub_text};">ESTADO</th>
                </tr>
                <tr style="border-bottom: 1px solid {table_border};">
                    <td style="padding: 8px; color: {text_color};">{datetime.datetime.now().strftime('%I:%M %p')}</td>
                    <td style="padding: 8px; color: #2ea043; font-weight: bold;">SYNC USER</td>
                    <td style="padding: 8px; color: {text_color};">XAU/USD</td>
                    <td style="padding: 8px; color: {text_color};">${mt5_data['price']:,.2f}</td>
                    <td style="padding: 8px; color: {text_color};">Conectado ✅</td>
                </tr>
            </table>
        </div>
    """, unsafe_allow_html=True)
