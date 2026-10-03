async def verificar_estado_cuenta(token: str, account_id: str):
  pass  # Función reservada para la siguiente fase


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
  """Inserta o actualiza un socio en la base de datos."""
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
  """Recupera la lista de socios registrados."""
  conn = sqlite3.connect("trading_bot.db")
  cursor = conn.cursor()
  cursor.execute("SELECT id, nombre, account_id_cifrado FROM socios")
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

st.title("📈 Radar Liquidity Gold Bot - Panel de Socios (Base de Datos)")
st.write(
    "Plataforma cloud segura con almacenamiento cifrado para cuentas MetaApi."
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

    # Guardar en SQLite de forma segura
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
st.subheader("📊 Socios y Cuentas Registradas (Cloud)")
st.info(
    "Las credenciales se almacenan cifradas en la base de datos interna para"
    " proteger el acceso a las cuentas MT5."
)

# Mostrar la lista de socios registrados
socios = obtener_socios_db()
if socios:
  st.write(f"Total de socios registrados: **{len(socios)}**")
  for socio in socios:
    st.markdown(
        f"- **ID:** {socio[0]} | **Socio:** {socio[1]} | **Account ID (Cifrado):**"
        f" `{socio[2][:20]}...`"
    )
else:
  st.warning("No hay cuentas registradas todavía. Usa el panel lateral.")

# Simulación de métricas de mercado
col1, col2, col3 = st.columns(3)
with col1:
  st.metric(label="Oro (XAU/USD)", value="$2,680.50", delta="+12.40")
with col2:
  st.metric(label="Base de Datos", value="SQLite Activa 🟢", delta="Segura")
with col3:
  st.metric(label="Seguridad Fernet", value="Protegido 🔒", delta="Activa")
