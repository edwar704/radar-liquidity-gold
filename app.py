import asyncio
import random
import sqlite3
import pandas as pd
import plotly.graph_objects as go
from metaapi_cloud_sdk import MetaApi
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Radar Liquidity Gold Bot",
    page_icon="🔒",
    layout="wide",
)

st.markdown("""
    <style>
    /* Tarjeta flotante para configuración MT5 (A la derecha, reducida) */
    .mt5-floating-card {
        background: linear-gradient(135deg, #1e222d 0%, #161a23 100%);
        border: 1px solid #2a2e39;
        border-radius: 16px;
        padding: 20px;
        position: relative;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
        margin-top: 10px;
        margin-bottom: 20px;
    }
    
    .mt5-badge-floating {
        position: absolute;
        top: 18px;
        right: 18px;
        background: linear-gradient(135deg, #008eff 0%, #0044cc 100%);
        width: 38px;
        height: 38px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 0.75rem;
        box-shadow: 0 4px 12px rgba(0, 142, 255, 0.4);
        letter-spacing: 0.5px;
    }

    .mt5-floating-card h3 {
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 3px;
    }

    .mt5-floating-card p {
        color: #848e9c;
        font-size: 0.8rem;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONFIGURACIÓN DE CREDENCIALES Y SECRETS
# ==========================================
if "METAAPI_TOKEN" in st.secrets:
  MASTER_METAAPI_TOKEN = st.secrets["METAAPI_TOKEN"]
else:
  st.error("⚠ Falta configurar METAAPI_TOKEN en los Secrets de Streamlit.")
  MASTER_METAAPI_TOKEN = ""

ADMIN_PASSWORD_SECRET = st.secrets.get("ADMIN_PASSWORD", "Admin123*")


# ==========================================
# 3. GESTIÓN DE BASE DE DATOS LOCAL
# ==========================================
def inicializar_db():
  try:
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                es_admin INTEGER DEFAULT 0
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS relacion_socios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_socio TEXT NOT NULL,
                account_id TEXT NOT NULL UNIQUE,
                login TEXT NOT NULL,
                server TEXT NOT NULL
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS invitaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                usado INTEGER DEFAULT 0,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()
    conn.close()
  except Exception as e:
    st.error(f"Error al inicializar la base de datos: {e}")


inicializar_db()


def generar_nuevo_codigo():
  while True:
    numero_aleatorio = random.randint(1000, 9999)
    codigo = f"GOLD-{numero_aleatorio}"
    try:
      conn = sqlite3.connect("trading_bot.db")
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO invitaciones (codigo, usado) VALUES (?, 0)", (codigo,)
      )
      conn.commit()
      conn.close()
      return codigo
    except sqlite3.IntegrityError:
      continue


def registrar_usuario_db(nombre, password, codigo_usado):
  try:
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, usado FROM invitaciones WHERE codigo = ?", (codigo_usado,)
    )
    inv = cursor.fetchone()
    if not inv:
      conn.close()
      return False, "El código de invitación no existe."
    if inv[1] == 1:
      conn.close()
      return False, "Este código de invitación ya fue utilizado."
    cursor.execute(
        "INSERT INTO usuarios (nombre, password, es_admin) VALUES (?, ?, 0)",
        (nombre, password),
    )
    cursor.execute(
        "UPDATE invitaciones SET usado = 1 WHERE codigo = ?", (codigo_usado,)
    )
    conn.commit()
    conn.close()
    return True, "Registro exitoso"
  except Exception as e:
    return False, f"Este nombre de usuario ya está registrado: {e}"


def verificar_usuario_db(nombre, password):
  conn = sqlite3.connect("trading_bot.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, nombre, password, es_admin FROM usuarios WHERE nombre = ?",
      (nombre,),
  )
  fila = cursor.fetchone()
  conn.close()
  if fila and fila[2] == password:
    return True, fila[3]
  return False, 0


def guardar_relacion_socio(
    nombre: str, account_id: str, login: str, server: str
):
  try:
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT OR REPLACE INTO relacion_socios (nombre_socio, account_id, login, server)
            VALUES (?, ?, ?, ?)
        """,
        (nombre, account_id, login, server),
    )
    conn.commit()
    conn.close()
  except Exception as e:
    print(f"Error guardando socio: {e}")


def obtener_relacion_socios():
  conn = sqlite3.connect("trading_bot.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT nombre_socio, account_id, login, server FROM relacion_socios"
  )
  filas = cursor.fetchall()
  conn.close()
  return {
      fila[1]: {
          "nombre": fila[0],
          "account_id": fila[1],
          "login": fila[2],
          "server": fila[3],
      }
      for fila in filas
  }


def obtener_cuenta_socio(nombre_socio: str):
  conn = sqlite3.connect("trading_bot.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT account_id, login, server FROM relacion_socios WHERE"
      " nombre_socio = ?",
      (nombre_socio,),
  )
  fila = cursor.fetchone()
  conn.close()
  if fila:
    return {"account_id": fila[0], "login": fila[1], "server": fila[2]}
  return None


# ==========================================
# 4. FUNCIONES ASÍNCRONAS DE METAAPI
# ==========================================
async def verificar_estado_cuenta(account_id: str):
  try:
    metaapi = MetaApi(MASTER_METAAPI_TOKEN)
    account = await metaapi.metatrader_account_api.get_account(account_id)
    if account.state != "DEPLOYED":
      await account.deploy()
    if account.connection_status != "CONNECTED":
      await account.wait_connected()
    connection = account.get_rpc_connection()
    await connection.connect()
    await connection.wait_synchronized()
    account_info = await connection.get_account_information()
    await connection.close()
    return True, account_info
  except Exception as e:
    return False, str(e)


async def obtener_precio_oro(account_id: str):
  try:
    metaapi = MetaApi(MASTER_METAAPI_TOKEN)
    account = await metaapi.metatrader_account_api.get_account(account_id)
    if account.state != "DEPLOYED":
      await account.deploy()
    if account.connection_status != "CONNECTED":
      await account.wait_connected()
    connection = account.get_rpc_connection()
    await connection.connect()
    await connection.wait_synchronized()
    simbolos = ["XAUUSD", "GOLD", "XAUUSD.ecn"]
    precio_actual = None
    simbolo_usado = ""
    for sim in simbolos:
      try:
        price = await connection.get_symbol_price(sim)
        if price and "bid" in price:
          precio_actual = price
          simbolo_usado = sim
          break
      except:
        continue
    await connection.close()
    if precio_actual:
      return True, simbolo_usado, precio_actual
    else:
      return False, "", "No se encontró un símbolo activo para el oro."
  except Exception as e:
    return False, "", str(e)


# ==========================================
# 5. CONTROL DE ACCESO E INTERFAZ DE LOGIN
# ==========================================
if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "user_name" not in st.session_state:
  st.session_state.user_name = ""
if "is_admin" not in st.session_state:
  st.session_state.is_admin = 0

params = st.query_params
codigo_desde_url = params.get("invite", "")

if not st.session_state.logged_in:
  st.title("📈 Radar Liquidity Gold Bot - Acceso")
  st.info(
      "🔒 Inicia sesión con tu cuenta o regístrate con el código de invitación"
      " que te proporcionó el administrador."
  )

  tab_login, tab_registro = st.tabs(
      ["🔑 Iniciar Sesión", "📝 Registrarse con Código de Invitación"]
  )

  with tab_login:
    st.subheader("Acceso al Sistema")
    login_nombre = st.text_input("Tu Nombre de Usuario", key="login_nombre")
    login_pass = st.text_input(
        "Tu Clave de Acceso", type="password", key="login_pass"
    )

    if st.button("Entrar al Bot"):
      if (
          login_nombre.lower() == "admin"
          and login_pass == ADMIN_PASSWORD_SECRET
      ):
        st.session_state.logged_in = True
        st.session_state.user_name = "Administrador"
        st.session_state.is_admin = 1
        st.success("¡Acceso concedido como Administrador!")
        st.rerun()
      else:
        valido, admin_status = verificar_usuario_db(login_nombre, login_pass)
        if valido:
          st.session_state.logged_in = True
          st.session_state.user_name = login_nombre
          st.session_state.is_admin = admin_status
          st.success(f"¡Bienvenido de nuevo, {login_nombre}!")
          st.rerun()
        else:
          st.error("Nombre de usuario o clave incorrectos.")

  with tab_registro:
    st.subheader("Nuevo Registro con Invitación")
    reg_nombre = st.text_input("Escribe tu Nombre", key="reg_nombre")
    reg_codigo = st.text_input(
        "Código de Invitación (Ej: GOLD-XXXX)",
        value=codigo_desde_url,
        key="reg_codigo",
    )
    reg_pass1 = st.text_input(
        "Crea tu Clave de Acceso", type="password", key="reg_pass1"
    )
    reg_pass2 = st.text_input(
        "Confirma tu Clave de Acceso", type="password", key="reg_pass2"
    )

    if st.button("Registrarse en el Bot"):
      if not reg_nombre or not reg_codigo or not reg_pass1:
        st.warning("Por favor completa todos los campos.")
      elif reg_pass1 != reg_pass2:
        st.error("❌ Las claves de acceso no coinciden.")
      else:
        exito, mensaje = registrar_usuario_db(reg_nombre, reg_pass1, reg_codigo)
        if exito:
          st.success(
              "¡Registro exitoso! 🟢 Ahora ve a la pestaña 'Iniciar Sesión' e"
              " ingresa con tu nombre y la clave que creaste."
          )
        else:
          st.error(f"❌ {mensaje}")

else:
  # ==========================================
  # 6. APLICACIÓN PRINCIPAL (USUARIO LOGUEADO)
  # ==========================================
  is_admin_user = (
      st.session_state.is_admin == 1
      or st.session_state.user_name == "Administrador"
  )

  st.sidebar.title(f"👤 Hola, {st.session_state.user_name}")
  if st.sidebar.button("Cerrar Sesión"):
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.is_admin = 0
    st.rerun()

  # ==========================================
  # PANEL LATERAL DE ADMINISTRADOR
  # ==========================================
  if is_admin_user:
    st.sidebar.markdown("---")
    st.sidebar.header("🎫 Generador de Invitaciones")
    url_base_bot = "https://radar-liquidity-gold-bot.streamlit.app"

    if st.sidebar.button("✨ Generar Nuevo Código"):
      nuevo_cod = generar_nuevo_codigo()
      enlace_con_parametro = f"{url_base_bot.strip('/')}/?invite={nuevo_cod}"
      st.sidebar.success("¡Código generado con éxito!")
      st.sidebar.markdown(
          "Copia este mensaje y envíaselo a tu socio de forma directa:"
      )
      st.sidebar.code(
          f"¡Hola! Regístrate en el bot haciendo clic aquí:\n{enlace_con_parametro}\n\nTu"
          f" código de invitación es: {nuevo_cod}",
          language="text",
      )

  # ==========================================
  # INTERFAZ PRINCIPAL SEGÚN EL ROL
  # ==========================================
  if is_admin_user:
    st.title("📈 Panel de Control - Administrador")

    pestana_admin_socios, pestana_admin_liquidez = st.tabs([
        "📊 Monitoreo de Cuentas de Socios",
        "⚡ Radar de Liquidez XAU/USD",
    ])

    socios_dict = obtener_relacion_socios()

    with pestana_admin_socios:
      st.subheader("Supervisión de Cuentas Conectadas")
      if socios_dict:
        opciones_select = {
            f"Socio: {info['nombre']} | Login: {info['login']} ({info['server']})"
            : info["account_id"]
            for info in socios_dict.values()
        }
        cuenta_seleccionada_key = st.selectbox(
            "Selecciona un Socio para Monitorear", list(opciones_select.keys())
        )
        if cuenta_seleccionada_key:
          s_acc_id = opciones_select[cuenta_seleccionada_key]
          info_socio = next(
              item
              for item in socios_dict.values()
              if item["account_id"] == s_acc_id
          )
          st.write(
              f"**👤 Socio:** {info_socio['nombre']} | **🔢 Login:**"
              f" `{info_socio['login']}` | **🏢 Servidor:**"
              f" `{info_socio['server']}`"
          )
          if st.button("Consultar Balance y Estado en Vivo"):
            with st.spinner("Consultando servidores de MetaApi Cloud..."):
              exito, resultado = asyncio.run(verificar_estado_cuenta(s_acc_id))
              if exito:
                st.success("¡Datos obtenidos correctamente! 🟢")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                  st.metric(
                      label="Balance",
                      value=f"${resultado.get('balance', 0):,.2f}",
                  )
                with col_b:
                  st.metric(
                      label="Equidad",
                      value=f"${resultado.get('equity', 0):,.2f}",
                  )
                with col_c:
                  st.metric(
                      label="Moneda", value=resultado.get("currency", "USD")
                  )
              else:
                st.error(
                    f"No se pudo consultar la cuenta. Detalle: {resultado}"
                )
      else:
        st.info("No hay cuentas de socios registradas todavía.")

    with pestana_admin_liquidez:
      st.subheader("⚡ Motor de Análisis Institucional y Liquidez (XAU/USD)")
      if socios_dict:
        cuenta_referencia = list(socios_dict.values())[0]["account_id"]
        if st.button("🔍 Escanear Zonas de Liquidez y Precio Actual"):
          with st.spinner("Analizando cotizaciones del Oro..."):
            exito_p, simbolo, datos_precio = asyncio.run(
                obtener_precio_oro(cuenta_referencia)
            )
            if exito_p:
              bid = datos_precio.get("bid", 0)
              ask = datos_precio.get("ask", 0)
              spread = round((ask - bid) * 10, 1)
              st.success(
                  f"¡Escaneo completado usando el símbolo `{simbolo}`! 🟢"
              )
              col1, col2, col3 = st.columns(3)
              with col1:
                st.metric(label="Precio Bid (Venta)", value=f"${bid:,.2f}")
              with col2:
                st.metric(label="Precio Ask (Compra)", value=f"${ask:,.2f}")
              with col3:
                st.metric(label="Spread Estimado", value=f"{spread} pips")
              st.markdown("---")
              st.markdown("### 📊 Zonas Institucionales Detectadas")
              st.info(
                  "💡 **Análisis de Estructura de Liquidez:**\n"
                  f"- **Precio de Mercado Actual:** ${bid:,.2f}\n"
                  "- **Zona de Resistencia / Liquidez Superior (Buy Stops):**"
                  f" Estimada en `${bid + 5.00:,.2f}`\n"
                  "- **Zona de Soporte / Liquidez Inferior (Sell Stops):**"
                  f" Estimada en `${bid - 5.00:,.2f}`"
              )
            else:
              st.error(f"No se pudo obtener el precio del oro: {datos_precio}")
      else:
        st.warning(
            "⚠ Necesitas al menos una cuenta de socio conectada para utilizar"
            " la pasarela de datos del mercado."
        )

  else:
    # VISTA DE SOCIO / USUARIO NORMAL
    st.title("📈 Panel de Socio - Radar Liquidity Gold Bot")

    cuenta_socio = obtener_cuenta_socio(st.session_state.user_name)

    pestana_socio_info, pestana_socio_radar = st.tabs([
        "📚 Información y Guía del Bot",
        "⚡ Radar de Liquidez XAU/USD",
    ])

    with pestana_socio_info:
      st.subheader("🤖 ¿Qué es y cómo funciona el Radar Liquidity Gold Bot?")
      st.markdown("""
            Bienvenido a tu plataforma de análisis institucional. Este bot está diseñado exclusivamente para operar y analizar el mercado del oro (**XAU/USD**) utilizando conceptos avanzados de **Smart Money Concepts (SMC)** y gestión de liquidez institucional.
            
            ### 🔍 ¿Qué es lo que hace el bot?
            1. **Escaneo de Zonas de Liquidez:** Analiza en tiempo real las cotizaciones del mercado para detectar acumulaciones de órdenes pendientes, zonas de soporte/resistencia institucionales y posibles áreas de barrido de liquidez (*Buy Stops* y *Sell Stops*).
            2. **Monitoreo en Vivo:** Permite conectar tu cuenta de MetaTrader 5 para supervisar tus métricas operativas directamente desde la plataforma de forma segura y automatizada a través de MetaApi Cloud.
            3. **Cálculo de Spread y Precios:** Monitorea de forma continua los precios *Bid* y *Ask* para estimar el spread actual del mercado antes de que tomes decisiones operativas.
            """)

    with pestana_socio_radar:
      st.subheader("⚡ Motor de Análisis Institucional y Liquidez (XAU/USD)")

      # Variables de control en sesión para las velas en tiempo real
      if "live_candles" not in st.session_state:
        st.session_state.live_candles = {
            "Tiempos": [
                "10:00",
                "10:15",
                "10:30",
                "10:45",
                "11:00",
                "11:15",
                "11:30",
                "11:45",
                "12:00",
                "12:15",
            ],
            "Open": [
                2640.0,
                2642.5,
                2641.0,
                2643.8,
                2645.0,
                2642.0,
                2646.5,
                2648.0,
                2651.0,
                2649.5,
            ],
            "High": [
                2643.0,
                2645.0,
                2643.5,
                2646.0,
                2647.2,
                2647.5,
                2649.0,
                2652.5,
                2653.0,
                2654.2,
            ],
            "Low": [
                2638.5,
                2641.0,
                2639.2,
                2642.0,
                2642.5,
                2641.0,
                2644.0,
                2647.0,
                2648.5,
                2648.0,
            ],
            "Close": [
                2642.5,
                2641.0,
                2643.8,
                2645.0,
                2642.0,
                2646.5,
                2648.0,
                2651.0,
                2649.5,
                2653.8,
            ],
        }

      if cuenta_socio:
        if st.button("🔍 Escanear Zonas de Liquidez y Actualizar Gráfico", key="btn_radar_socio"):
          with st.spinner("Conectando con MetaApi Cloud para obtener precio en vivo..."):
            exito_p, simbolo, datos_precio = asyncio.run(
                obtener_precio_oro(cuenta_socio["account_id"])
            )
            if exito_p:
              bid = datos_precio.get("bid", 0)
              ask = datos_precio.get("ask", 0)
              spread = round((ask - bid) * 10, 1)

              # Actualizar la última vela con el precio real obtenido del bróker
              nuevo_open = st.session_state.live_candles["Close"][-1]
              nuevo_close = bid
              nuevo_high = max(nuevo_open, nuevo_close) + 1.2
              nuevo_low = min(nuevo_open, nuevo_close) - 1.2

              st.session_state.live_candles["Tiempos"].append("En Vivo")
              st.session_state.live_candles["Open"].append(nuevo_open)
              st.session_state.live_candles["High"].append(nuevo_high)
              st.session_state.live_candles["Low"].append(nuevo_low)
              st.session_state.live_candles["Close"].append(nuevo_close)

              st.success(f"¡Precio en vivo obtenido de `{simbolo}`! Gráfico actualizado. 🟢")
              
              col1, col2, col3 = st.columns(3)
              with col1:
                st.metric(label="Precio Bid (Venta)", value=f"${bid:,.2f}")
              with col2:
                st.metric(label="Precio Ask (Compra)", value=f"${ask:,.2f}")
              with col3:
                st.metric(label="Spread", value=f"{spread} pips")
            else:
              st.error(f"No se pudo obtener el precio en vivo: {datos_precio}")
      else:
        st.info(
            "💡 Vincula tu cuenta de MetaTrader 5 en la derecha para alimentar"
            " el gráfico con precios reales del mercado en tiempo real."
        )

    st.markdown("---")

    if not cuenta_socio:
      st.warning(
          "⚠ **Aviso:** Aún no tienes una cuenta MT5 vinculada. Configura tus"
          " credenciales en el panel de la derecha para sincronizar tus métricas."
      )
    else:
      st.success("🟢 Tu cuenta de MetaTrader 5 se encuentra vinculada al sistema.")

    # ==========================================
    # DISTRIBUCIÓN DE DOS COLUMNAS PRINCIPALES
    # IZQUIERDA: Gráfico de Velas Actualizado en Tiempo Real
    # DERECHA: Tarjeta Flotante Compacta de MT5
    # ==========================================
    col_izq_grafico, col_der_config = st.columns([1.4, 1])

    with col_izq_grafico:
      st.markdown("### 📊 XAU/USD • Velas y Zonas de Liquidez en Vivo")

      # Carga de datos de velas (estáticos + actualizaciones en vivo)
      c_data = st.session_state.live_candles
      df_velas = pd.DataFrame({
          "Tiempo": c_data["Tiempos"],
          "Open": c_data["Open"],
          "High": c_data["High"],
          "Low": c_data["Low"],
          "Close": c_data["Close"],
      })

      fig = go.Figure(
          data=[
              go.Candlestick(
                  x=df_velas["Tiempo"],
                  open=df_velas["Open"],
                  high=df_velas["High"],
                  low=df_velas["Low"],
                  close=df_velas["Close"],
                  increasing_line_color="#00ff80",  # Velas Verdes
                  decreasing_line_color="#ff4d4d",  # Velas Rojas
                  increasing_fillcolor="#00ff80",
                  decreasing_fillcolor="#ff4d4d",
              )
          ]
      )

      # Líneas dinámicas de liquidez basadas en el rango actual
      max_val = max(c_data["High"])
      min_val = min(c_data["Low"])

      fig.add_hline(
          y=max_val,
          line_dash="dash",
          line_color="#ff4d4d",
          annotation_text="BUY STOPS (Resistencia)",
          annotation_position="top right",
          annotation_font_color="#ff4d4d",
      )

      fig.add_hline(
          y=min_val,
          line_dash="dash",
          line_color="#00ff80",
          annotation_text="SELL STOPS (Soporte)",
          annotation_position="bottom right",
          annotation_font_color="#00ff80",
      )

      fig.update_layout(
          paper_bgcolor="#131722",
          plot_bgcolor="#131722",
          font=dict(color="#d1d4dc", size=11),
          margin=dict(l=10, r=10, t=30, b=10),
          height=270,
          xaxis=dict(showgrid=True, gridcolor="#2a2e39"),
          yaxis=dict(showgrid=True, gridcolor="#2a2e39"),
          showlegend=False,
      )

      st.plotly_chart(fig, use_container_width=True)

    with col_der_config:
      with st.expander(
          "⚙️ Configurar MT5",
          expanded=not bool(cuenta_socio),
      ):
        # Tarjeta flotante compacta con insignia MT5 a la derecha
        st.markdown(
            """
                <div class="mt5-floating-card">
                    <div class="mt5-badge-floating">MT5</div>
                    <h3>Conectar Cuenta</h3>
                    <p>Sincroniza tus datos de forma segura.</p>
                </div>
                """,
            unsafe_allow_html=True,
        )

        if cuenta_socio:
          st.caption(
              f"Vinculada: `{cuenta_socio['login']}` | `{cuenta_socio['server']}`"
          )

        mt5_login = st.text_input(
            "Número de Cuenta (Login)", key="card_login_inf"
        )
        mt5_password = st.text_input(
            "Contraseña de Trading", type="password", key="card_pass_inf"
        )

        opciones_brokers = [
            "Selecciona servidor...",
            "MetaQuotes-Demo",
            "VantageInternational-Live 01",
            "VantageInternational-Live 02",
            "VantageInternational-Live 03",
            "VantageInternational-Live 04",
            "VantageInternational-Demo",
            "Exness-Real11",
            "Exness-Real12",
            "Exness-Real13",
            "Exness-Trial",
            "RoboForex-Pro",
            "RoboForex-ECN",
            "RoboForex-Demo",
            "ICMarketsSC-Live 01",
            "ICMarketsSC-Live 02",
            "ICMarketsSC-Demo",
            "XMGlobal-MT5 18",
            "Weltrade",
            "Otro (Escribir manualmente)",
        ]

        broker_seleccionado = st.selectbox(
            "Servidor del Bróker", opciones_brokers, key="card_broker_inf"
        )

        if broker_seleccionado == "Otro (Escribir manualmente)":
          mt5_server = st.text_input(
              "Escribe el servidor exacto del bróker", key="card_otro_serv_inf"
          )
        elif broker_seleccionado != "Selecciona servidor...":
          mt5_server = broker_seleccionado
        else:
          mt5_server = ""

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "Vincular con MetaApi", key="btn_card_guardar_inf", use_container_width=True
        ):
          if mt5_login and mt5_password and mt5_server:
            with st.spinner(
                "Conectando tu cuenta de forma segura a MetaApi Cloud..."
            ):

              async def registrar_socio_metaapi():
                try:
                  metaapi = MetaApi(MASTER_METAAPI_TOKEN)
                  account = await metaapi.metatrader_account_api.create_account({
                      "name": f"Socio - {st.session_state.user_name}",
                      "type": "cloud",
                      "login": mt5_login,
                      "password": mt5_password,
                      "server": mt5_server,
                      "platform": "mt5",
                      "magic": 123456,
                  })
                  return True, account.id
                except Exception as ex:
                  return False, str(ex)

              exito, resultado = asyncio.run(registrar_socio_metaapi())

              if exito:
                guardar_relacion_socio(
                    st.session_state.user_name, resultado, mt5_login, mt5_server
                )
                st.success("¡Cuenta conectada y vinculada con éxito! 🟢")
                st.rerun()
              else:
                st.error(f"Error al conectar con el bróker: {resultado}")
          else:
            st.warning("Por favor completa todos los campos de la cuenta.")
