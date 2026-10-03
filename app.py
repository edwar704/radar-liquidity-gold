import asyncio
from cryptography.fernet import Fernet
import sqlite3
from metaapi_cloud_sdk import MetaApi
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Radar Liquidity Gold Bot",
    page_icon="📈",
    layout="wide",
)

# ==========================================
# 2. CONFIGURACIÓN DE CREDENCIALES
# ==========================================
if "METAAPI_TOKEN" in st.secrets:
  MASTER_METAAPI_TOKEN = st.secrets["METAAPI_TOKEN"]
else:
  st.error("⚠ Falta configurar METAAPI_TOKEN en los Secrets de Streamlit.")
  MASTER_METAAPI_TOKEN = ""

# ==========================================
# 3. GESTIÓN DE BASE DE DATOS SQLITE LOCAL
# ==========================================


def inicializar_db():
  """Elimina la tabla anterior y la crea limpia para evitar conflictos."""
  try:
    conn = sqlite3.connect("trading_bot.db")
    cursor = conn.cursor()
    # Forzar la recreación limpia de la tabla de socios
    cursor.execute("DROP TABLE IF EXISTS socios")
    cursor.execute("""
            CREATE TABLE socios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                account_id TEXT NOT NULL,
                login TEXT NOT NULL,
                server TEXT NOT NULL
            )
        """)
    conn.commit()
    conn.close()
  except Exception as e:
    st.error(f"Error al inicializar la base de datos: {e}")


def guardar_socio_db(
    nombre: str, account_id: str, login: str, server: str
):
  """Guarda una cuenta registrada en la base de datos local."""
  conn = sqlite3.connect("trading_bot.db")
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO socios (nombre, account_id, login, server)
        VALUES (?, ?, ?, ?)
    """,
      (nombre, account_id, login, server),
  )
  conn.commit()
  conn.close()


def obtener_socios_db():
  """Recupera la lista de cuentas guardadas localmente."""
  conn = sqlite3.connect("trading_bot.db")
  cursor = conn.cursor()
  cursor.execute("SELECT id, nombre, account_id, login, server FROM socios")
  filas = cursor.fetchall()
  conn.close()
  return filas


# Inicializar base de datos limpia al arrancar
inicializar_db()

# ==========================================
# 4. FUNCIONES ASÍNCRONAS DE METAAPI
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


# ==========================================
# 5. INTERFAZ DE USUARIO (UI)
# ==========================================
st.title(
    "📈 Radar Liquidity Gold Bot - Onboarding Automático de Cuentas MT5"
)
st.write(
    "Conexión inteligente y automatizada de cuentas de trading mediante"
    " MetaApi."
)

# Panel Lateral: Registro Automático
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
              "name": f"Bot - {socio_nombre}",
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
        guardar_socio_db(
            socio_nombre, account_id_generado, mt5_login, mt5_server
        )
        st.sidebar.success(
            f"¡Cuenta para {socio_nombre} conectada y registrada con éxito! 🟢"
        )
        st.rerun()
      else:
        st.sidebar.error(f"Error al conectar con el bróker: {resultado}")
  else:
    st.sidebar.warning("Por favor completa todos los campos.")

# Panel Principal: Monitoreo de Cuentas Locales
st.subheader("📊 Monitoreo de Cuentas Conectadas")

socios = obtener_socios_db()
if socios:
  nombres_socios = {
      f"{socio[1]} (Login: {socio[3]})": socio for socio in socios
  }
  socio_seleccionado_key = st.selectbox(
      "Selecciona un Socio para Monitorear", list(nombres_socios.keys())
  )

  if socio_seleccionado_key:
    s_id, s_nombre, s_acc_id, s_login, s_server = nombres_socios[
        socio_seleccionado_key
    ]
    st.write(
        f"**Socio:** {s_nombre} | **Login:** `{s_login}` | **Account ID:**"
        f" `{s_acc_id}`"
    )

    if st.button("Consultar Balance y Estado en Vivo"):
      with st.spinner("Consultando servidores de MetaApi Cloud..."):
        exito, resultado = asyncio.run(verificar_estado_cuenta(s_acc_id))

        if exito:
          st.success("¡Datos obtenidos correctamente! 🟢")
          col_a, col_b, col_c = st.columns(3)
          with col_a:
            st.metric(
                label="Balance", value=f"${resultado.get('balance', 0):,.2f}"
            )
          with col_b:
            st.metric(
                label="Equidad", value=f"${resultado.get('equity', 0):,.2f}"
            )
          with col_c:
            st.metric(label="Moneda", value=resultado.get('currency', 'USD'))
        else:
          st.error(
              f"No se pudo consultar la cuenta. Detalle: {resultado}"
          )
else:
  st.warning(
      "No hay cuentas registradas todavía. Utiliza el panel lateral para"
      " registrar tu primera cuenta."
  )

# Métricas generales de mercado
st.markdown("---")
st.subheader("📈 Mercado de Referencia")
col1, col2, col3 = st.columns(3)
with col1:
  st.metric(label="Oro (XAU/USD)", value="$2,680.50", delta="+12.40")
with col2:
  st.metric(label="Infraestructura Cloud", value="Activa 🟢", delta="MetaApi")
with col3:
  st.metric(label="Onboarding", value="Automático ⚡", delta="Habilitado")
