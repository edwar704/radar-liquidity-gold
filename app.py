import asyncio
import random
import sqlite3
from metaapi_cloud_sdk import MetaApi
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Radar Liquidity Gold Bot",
    page_icon="🔒",
    layout="wide",
)

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
    # Tabla de usuarios registrados
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                es_admin INTEGER DEFAULT 0
            )
        """)
    # Tabla para relacionar socios y sus cuentas de MetaApi
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS relacion_socios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_socio TEXT NOT NULL,
                account_id TEXT NOT NULL UNIQUE,
                login TEXT NOT NULL,
                server TEXT NOT NULL
            )
        """)
    # Tabla para almacenar códigos de invitación generados por el admin
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
  """Genera un código aleatorio único y lo guarda en la base de datos."""
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
  # PANEL LATERAL DE ADMINISTRADOR (Enlace fijo)
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
    # VISTA DE ADMINISTRADOR
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
    # VISTA DE SOCIO / USUARIO NORMAL (Nuevo flujo no invasivo)
    st.title("📈 Panel de Socio - Radar Liquidity Gold Bot")

    cuenta_socio = obtener_cuenta_socio(st.session_state.user_name)

    # 1. Bienvenida y opción desplegable no intrusiva para conectar MT5
    if not cuenta_socio:
      st.info(
          "👋 **¡Bienvenido a la comunidad!** Ya puedes explorar las funciones"
          " informativas del bot. Cuando desees conectar tu cuenta de"
          " MetaTrader 5 para sincronizar tus operaciones y métricas en vivo,"
          " despliega la sección de abajo."
      )
    else:
      st.success("🟢 Tu cuenta de MetaTrader 5 se encuentra vinculada al sistema.")

    # Desplegable para gestionar la conexión MT5 en cualquier momento
    with st.expander(
        "⚙️ Configuración y Conexión de mi Cuenta MetaTrader 5 (MT5)",
        expanded=not bool(cuenta_socio),
    ):
      if cuenta_socio:
        st.write(
            f"**Cuenta Actual Vinculada:** Login: `{cuenta_socio['login']}` |"
            f" Servidor: `{cuenta_socio['server']}`"
        )
        st.markdown("Si deseas actualizarla o cambiarla, ingresa los nuevos datos:")

      mt5_login = st.text_input("Número de Cuenta (Login)", key="exp_login")
      mt5_password = st.text_input(
          "Contraseña de Trading", type="password", key="exp_pass"
      )

      opciones_brokers = [
          "Selecciona o escribe...",
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
          "Otro (Escribir manualmente)",
      ]

      broker_seleccionado = st.selectbox(
          "Servidor del Bróker", opciones_brokers, key="exp_broker"
      )

      if broker_seleccionado == "Otro (Escribir manualmente)":
        mt5_server = st.text_input(
            "Escribe el servidor exacto del bróker", key="exp_otro_serv"
        )
      elif broker_seleccionado != "Selecciona o escribe...":
        mt5_server = broker_seleccionado
      else:
        mt5_server = ""

      if st.button("Guardar y Conectar Cuenta MT5"):
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

    st.markdown("---")

    # 2. Pestañas de contenido del bot para el socio
    pestana_ socio_info, pestana_socio_radar = st.tabs([
        "📚 Información y Guía del Bot",
        "⚡ Radar de Liquidez XAU/USD",
    ])

    with pestana_socio_info:
      st.subheader("Bienvenido al Radar Liquidity Gold")
      st.markdown("""
            Este bot está diseñado para ayudarte a identificar las mejores zonas institucionales de liquidez en el mercado del oro (**XAU/USD**).
            
            * **¿Cómo empezar?** Puedes explorar el análisis de liquidez en la pestaña contigua.
            * **Conexión opcional:** Si deseas consultar los balances y estados en tiempo real de tus operaciones, vincula tu cuenta MT5 utilizando el menú desplegable superior en el momento que consideres oportuno.
            """)

    with pestana_socio_radar:
      st.subheader("⚡ Motor de Análisis Institucional y Liquidez (XAU/USD)")
      if cuenta_socio:
        if st.button("🔍 Escanear Zonas de Liquidez", key="btn_radar_socio"):
          with st.spinner("Analizando cotizaciones del Oro..."):
            exito_p, simbolo, datos_precio = asyncio.run(
                obtener_precio_oro(cuenta_socio["account_id"])
            )
            if exito_p:
              bid = datos_precio.get("bid", 0)
              ask = datos_precio.get("ask", 0)
              spread = round((ask - bid) * 10, 1)
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
        st.info(
            "💡 Actualmente estás explorando el bot en modo libre. Para usar"
            " el escáner de liquidez en vivo, vincula tu cuenta de MetaTrader 5"
            " en la sección superior desplegable."
        )
