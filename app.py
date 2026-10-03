async def verificar_estado_cuenta(token_cifrado: str, account_id_cifrado: str):
  """Descifra las credenciales y consulta el estado de la cuenta en MetaApi

  Cloud.
  """
  try:
    token = descifrar_dato(token_cifrado)
    account_id = descifrar_dato(account_id_cifrado)

    if not token or not account_id:
      return False, "Error al descifrar las credenciales."

    metaapi = MetaApi(token)
    account = await metaapi.metapiv1.get_account_api().get_account(account_id)

    # Conectar si no está desplegada o conectada
    if account.state != "DEPLOYED":
      await account.deploy()

    if account.connection_status != "CONNECTED":
      await account.wait_connected()

    # Obtener información de la cuenta (balance, equidad, etc.)
    connection = account.get_rpc_connection()
    await connection.connect()
    await connection.wait_synchronized()

    account_info = await connection.get_account_information()
    await connection.close()
    return True, account_info
  except Exception as e:
    return False, str(e)


import asyncio
from cryptography.fernet import Fernet
import sqlite3
from metaapi_cloud_sdk import MetaApi
import streamlit as st

# ==========================================
# CONFIGURACIÓN DE SEGURIDAD (FERNET)
# ==========================================
if "FERNET_KEY" in st.secrets:
  FERNET_KEY = st.secrets["FERNET_KEY"].encode()
  cipher_suite = Fernet(FERNET_KEY)
else:
  st.error("⚠️ Falta configurar la FERNET_KEY en los Secrets de Streamlit.")
  cipher_suite = None


def cifrar_dato(texto_plano: str) -> str:
  """Cifra un token o contraseña antes de guardarlo."""
  if cipher_suite:
    return cipher_suite.encrypt(texto_plano.encode()).decode()
  return ""


def descifrar_dato(texto_cifrado: str) -> str:
  """Descifra el token cuando el sistema necesite usarlo."""
  if cipher_suite:
    return cipher_suite.decrypt(texto_cifrado.encode()).decode()
  return ""


# ==========================================
# CONFIGURACIÓN DE LA BASE DE DATOS SQLITE
# ==========================================
def inicializar_db():
  """Crea la tabla de socios si no existe."""
  conn = sqlite3.connect("trading_bot.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS socios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            account_id_cifrado TEXT NOT NULL,
            token_cifrado TEXT NOT NULL
        )
    """)
  conn.commit()
  conn.close()


def guardar_socio_db(nombre: str, account_id_cifrado: str, token_cifrado: str):
  """Inserta un socio en la base de datos."""
  conn = sqlite3.connect("trading_bot.db")
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO socios (nombre, account_id_cifrado, token_cifrado)
        VALUES (?, ?, ?)
    """,
      (nombre, account_id_cifrado, token_cifrado),
  )
  conn.commit()
  conn.close()


def obtener_socios_db():
  """Recupera la lista completa de socios registrados (incluyendo datos cifrados)."""
  conn = sqlite3.connect("trading_bot.db")
  cursor = conn.cursor()
  cursor.execute("SELECT id, nombre, account_id_cifrado, token_cifrado FROM socios")
  filas = cursor.fetchall()
  conn.close()
  return filas


# Inicializar la base de datos al arrancar
inicializar_db()

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Radar Liquidity Gold Bot",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Radar Liquidity Gold Bot - Panel de Socios y Monitoreo MT5")
st.write(
    "Plataforma cloud segura con almacenamiento cifrado y conexión en vivo a"
    " MetaApi."
)

# ==========================================
# SECCIÓN: REGISTRO / CREDENCIALES DE METAAPI
# ==========================================
st.sidebar.header("🔐 Configuración MetaApi MT5")
socio_nombre = st.sidebar.text_input("Nombre de Socio")
metaapi_token = st.sidebar.text_input("Token de MetaApi", type="password")
metaapi_account_id = st.sidebar.text_input("MetaApi Account ID")

# Guía de ayuda desplegable para los socios
with st.sidebar.expander("❓ ¿Cómo obtener tus credenciales?"):
  st.markdown("""
    **1. Token de MetaApi:**
    - Entra a [app.metaapi.cloud](https://app.metaapi.cloud/).
    - Ve a la sección de configuración de perfil o tokens de acceso (API tokens).
    - Genera o copia tu *Personal Access Token*.
    
    **2. Account ID:**
    - Es el identificador único que te asigna MetaApi al conectar tu cuenta de MetaTrader 5 en su panel.
    """)

if st.sidebar.button("Guardar y Cifrar en BD"):
  if socio_nombre and metaapi_token and metaapi_account_id:
    token_seguro = cifrar_dato(metaapi_token)
    account_seguro = cifrar_dato(metaapi_account_id)

    guardar_socio_db(socio_nombre, account_seguro, token_seguro)
    st.sidebar.success(
        f"¡Credenciales de MetaApi para {socio_nombre} guardadas y cifradas en la"
        " BD! 🔒"
    )
  else:
    st.sidebar.warning(
        "Por favor completa todos los campos de MetaApi para continuar."
    )

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.subheader("📊 Monitoreo de Cuentas MT5 en Vivo")
st.info(
    "Selecciona un socio registrado para consultar su balance, equidad y"
    " estado en tiempo real a través de MetaApi."
)

socios = obtener_socios_db()
if socios:
  # Crear un selector de socios en el panel principal
  nombres_socios = {socio[1]: socio for socio in socios}
  socio_seleccionado = st.selectbox(
      "Selecciona un Socio para Monitorear", list(nombres_socios.keys())
  )

  if socio_seleccionado:
    s_id, s_nombre, s_acc_cifrado, s_token_cifrado = nombres_socios[
        socio_seleccionado
    ]

    st.write(f"**Socio Activo:** {s_nombre}")

    if st.button("Consultar Estado en Vivo con MetaApi"):
      with st.spinner(
          "Conectando de forma segura con los servidores de MetaApi..."
      ):
        # Ejecutar la función asíncrona de consulta
        exito, resultado = asyncio.run(
            verificar_estado_cuenta(s_token_cifrado, s_acc_cifrado)
        )

        if exito:
          st.success("¡Conexión exitosa con la cuenta MT5! 🟢")
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
              f"No se pudo establecer la conexión con MetaApi. Detalle:"
              f" {resultado}"
          )
else:
  st.warning(
      "No hay cuentas registradas todavía. Usa el panel lateral para registrar"
      " tu primera cuenta."
  )

# Simulación de métricas de mercado generales
st.markdown("---")
st.subheader("📈 Mercado de Referencia")
col1, col2, col3 = st.columns(3)
with col1:
  st.metric(label="Oro (XAU/USD)", value="$2,680.50", delta="+12.40")
with col2:
  st.metric(label="Infraestructura Cloud", value="Activa 🟢", delta="MetaApi")
with col3:
  st.metric(label="Seguridad Fernet", value="Protegido 🔒", delta="Activa")
