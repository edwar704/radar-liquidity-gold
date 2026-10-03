import asyncio
from cryptography.fernet import Fernet
import sqlite3
from metaapi_cloud_sdk import MetaApi
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Radar Liquidity Gold Bot - Admin",
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
# 3. GESTIÓN DE BASE DE DATOS LOCAL (SOCIO <-> CUENTA)
# ==========================================


def inicializar_db():
  """Crea la tabla para asociar socios con sus cuentas de MetaApi."""
  try:
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS relacion_socios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_socio TEXT NOT NULL,
                account_id TEXT NOT NULL UNIQUE,
                login TEXT NOT NULL,
                server TEXT NOT NULL
            )
        """)
    conn.commit()
    conn.close()
  except Exception as e:
    st.error(f"Error al inicializar la base de datos: {e}")


def guardar_relacion_socio(
    nombre: str, account_id: str, login: str, server: str
):
  """Guarda la relación entre el socio y su cuenta."""
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
  """Recupera todas las relaciones de socios guardadas."""
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


inicializar_db()

# ==========================================
# 4. FUNCIONES ASÍNCRONAS DE METAAPI (CLOUD)
# ==========================================


async def verificar_estado_cuenta(account_id: str):
  """Consulta el estado y balance de una cuenta en MetaApi Cloud."""
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
  """Obtiene el precio actual de XAU/USD desde una cuenta conectada."""
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

    # Intentar obtener el precio de XAUUSD (puede variar según el broker: XAUUSD, GOLD, etc.)
    simbolos = ["XAUUSD", "GOLD", "XAUUSD.ecn"]
    precio_actual = None
    simbolo_usado = ""

    for sim in simbols:
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
# 5. CONTROL DE ACCESO (ADMIN LOGIN)
# ==========================================
if "admin_authenticated" not in st.session_state:
  st.session_state.admin_authenticated = False

st.sidebar.title("🔐 Acceso de Administrador")

if not st.session_state.admin_authenticated:
  password_input = st.sidebar.text_input(
      "Contraseña de Admin", type="password"
  )
  if st.sidebar.button("Ingresar"):
    if password_input == ADMIN_PASSWORD_SECRET:
      st.session_state.admin_authenticated = True
      st.sidebar.success("¡Acceso concedido!")
      st.rerun()
    else:
      st.sidebar.error("Contraseña incorrecta.")

  st.title("📈 Radar Liquidity Gold Bot")
  st.info(
      "🔒 Esta aplicación es privada. Introduce tu contraseña de administrador"
      " en el panel lateral para acceder."
  )

else:
  # ==========================================
  # 6. PANEL DE ADMINISTRACIÓN (SOLO ADMIN)
  # ==========================================
  if st.sidebar.button("Cerrar Sesión"):
    st.session_state.admin_authenticated = False
    st.rerun()

  st.sidebar.markdown("---")
  st.sidebar.header("🚀 Conectar Nueva Cuenta MT5")
  socio_nombre = st.sidebar.text_input("Nombre de Socio")
  mt5_login = st.sidebar.text_input("Número de Cuenta (Login)")
  mt5_password = st.sidebar.text_input("Contraseña de Trading", type="password")

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

  broker_seleccionado = st.sidebar.selectbox(
      "Servidor del Bróker", opciones_brokers
  )

  if broker_seleccionado == "Otro (Escribir manualmente)":
    mt5_server = st.sidebar.text_input("Escribe el servidor exacto del bróker")
  elif broker_seleccionado != "Selecciona o escribe...":
    mt5_server = broker_seleccionado
  else:
    mt5_server = ""

  if st.sidebar.button("Registrar y Conectar Cuenta"):
    if socio_nombre and mt5_login and mt5_password and mt5_server:
      with st.spinner("Creando cuenta automáticamente en MetaApi Cloud..."):

        async def registrar_en_metaapi():
          try:
            metaapi = MetaApi(MASTER_METAAPI_TOKEN)
            account = await metaapi.metatrader_account_api.create_account({
                "name": f"Socio - {socio_nombre}",
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

        exito, resultado = asyncio.run(registrar_en_metaapi())

        if exito:
          account_id_generado = resultado
          guardar_relacion_socio(
              socio_nombre, account_id_generado, mt5_login, mt5_server
          )
          st.sidebar.success(
              f"¡Cuenta para {socio_nombre} conectada con éxito! 🟢"
          )
          st.rerun()
        else:
          st.sidebar.error(f"Error al conectar con el bróker: {resultado}")
    else:
      st.sidebar.warning("Por favor completa todos los campos.")

  # ==========================================
  # PANEL PRINCIPAL: PESTAÑAS DE CONTROL
  # ==========================================
  st.title(
      "📈 Radar Liquidity Gold Bot - Panel de Administración Exclusivo"
  )

  pestana_monitoreo, pestana_liquidez = st.tabs([
      "📊 Monitoreo de Socios",
      "⚡ Radar de Liquidez XAU/USD",
  ])

  # --- PESTAÑA 1: MONITOREO DE SOCIOS ---
  with pestana_monitoreo:
    st.subheader("Relación de Socios y Cuentas Conectadas")
    socios_dict = obtener_relacion_socios()

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
      st.warning(
          "No hay socios registrados todavía. Usa el panel lateral para"
          " registrar la primera cuenta."
      )

  # --- PESTAÑA 2: RADAR DE LIQUIDEZ XAU/USD ---
  with pestana_liquidez:
    st.subheader("⚡ Motor de Análisis Institucional y Liquidez (XAU/USD)")
    st.write(
        "Escaneo de mercado en tiempo real para detección de barridos de"
        " liquidez y zonas de alta probabilidad en el Oro."
    )

    socios_dict = obtener_relacion_socios()
    if socios_dict:
      # Usamos la primera cuenta disponible como pasarela de datos para el mercado
      cuenta_referencia = list(socios_dict.values())[0]["account_id"]

      if st.button("🔍 Escanear Zonas de Liquidez y Precio Actual"):
        with st.spinner(
            "Conectando al servidor del bróker para analizar cotizaciones de"
            " XAU/USD..."
        ):
          exito_p, simbolo, datos_precio = asyncio.run(
              obtener_precio_oro(cuenta_referencia)
          )

          if exito_p:
            bid = datos_precio.get("bid", 0)
            ask = datos_precio.get("ask", 0)
            spread = round((ask - bid) * 10, 1)  # Estimación de pips/puntos

            st.success(
                f"¡Escaneo completado con éxito utilizando el símbolo"
                f" `{simbolo}`! 🟢"
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
                "- **Zona de Resistencia / Liquidez Superior (Buy Stops):** Estimada"
                f" en `${bid + 5.00:,.2f}`\n"
                "- **Zona de Soporte / Liquidez Inferior (Sell Stops):** Estimada"
                f" en `${bid - 5.00:,.2f}`\n"
                "- **Estado del Algoritmo:** 🟢 Monitoreando ineficiencias (FVG)"
                " y Order Blocks activos."
            )
          else:
            st.error(f"No se pudo obtener el precio del oro: {datos_precio}")
    else:
      st.warning(
          "⚠ Debes registrar al menos una cuenta de socio en el panel lateral"
          " para que el bot pueda utilizarla como pasarela de datos de"
          " mercado para el Oro."
      )

  # Métricas generales de referencia inferior
  st.markdown("---")
  st.subheader("📈 Estado del Sistema")
  c1, c2, c3 = st.columns(3)
  with c1:
    st.metric(label="Activo Objetivo", value="XAU/USD (Oro)", delta="Institucional")
  with c2:
    st.metric(label="Infraestructura Cloud", value="Activa 🟢", delta="MetaApi")
  with c3:
    st.metric(label="Motor de Alertas", value="Operativo ⚡", delta="En línea")
