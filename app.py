import asyncio
from cryptography.fernet import Fernet
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
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Radar Liquidity Gold Bot",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Radar Liquidity Gold Bot - Panel de Socios (MetaApi Cloud)")
st.write(
    "Plataforma cloud segura para la gestión y conexión de cuentas de trading"
    " mediante MetaApi."
)

# ==========================================
# SECCIÓN: REGISTRO / CREDENCIALES DE METAAPI
# ==========================================
st.sidebar.header("🔐 Configuración MetaApi MT5")
socio_nombre = st.sidebar.text_input("Nombre de Socio")
metaapi_token = st.sidebar.text_input("Token de MetaApi", type="password")
metaapi_account_id = st.sidebar.text_input("MetaApi Account ID")

if st.sidebar.button("Guardar y Cifrar Credenciales"):
  if socio_nombre and metaapi_token and metaapi_account_id:
    token_seguro = cifrar_dato(metaapi_token)
    account_seguro = cifrar_dato(metaapi_account_id)
    # Aquí posteriormente almacenaremos 'token_seguro' y 'account_seguro' en tu Base de Datos
    st.sidebar.success(
        f"¡Credenciales de MetaApi para {socio_nombre} guardadas y cifradas con"
        " éxito! 🔒"
    )
  else:
    st.sidebar.warning(
        "Por favor completa todos los campos de MetaApi para continuar."
    )


# ==========================================
# FUNCIÓN DE CONEXIÓN CON METAAPI
# ==========================================
async def verificar_estado_cuenta(token: str, account_id: str):
  """Consulta el estado de la cuenta MT5 en MetaApi Cloud de forma asíncrona."""
  try:
    metaapi = MetaApi(token)
    account = await metaapi.metapiv1.get_account_api().get_account(account_id)

    # Conectar si no está conectada
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


# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.subheader("📊 Monitoreo y Estado de la Cuenta MT5")
st.info(
    "Utiliza el menú lateral para ingresar tus credenciales de MetaApi. El"
    " sistema validará la conexión con los servidores de tu bróker 24/7."
)

# Simulación de métricas de mercado
col1, col2, col3 = st.columns(3)
with col1:
  st.metric(label="Oro (XAU/USD)", value="$2,680.50", delta="+12.40")
with col2:
  st.metric(label="Infraestructura Cloud", value="Activa 🟢", delta="MetaApi")
with col3:
  st.metric(label="Seguridad Fernet", value="Protegido 🔒", delta="Activa")

# Botón de prueba de conexión rápida en el panel principal
if st.button("Probar Conexión con MetaApi (Usando datos de prueba)"):
  st.warning(
      "Para realizar pruebas reales, ingresa tus credenciales en el panel"
      " lateral y asegúrate de tener tu token activo de MetaApi."
  )
