from cryptography.fernet import Fernet
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

st.title("📈 Radar Liquidity Gold Bot - Panel de Socios")
st.write(
    "Plataforma cloud segura para la gestión y conexión de cuentas de trading."
)

# ==========================================
# SECCIÓN: REGISTRO / CONFIGURACIÓN DE CREDENCIALES
# ==========================================
st.sidebar.header("🔐 Gestión de Cuenta MT5")
socio_nombre = st.sidebar.text_input("Nombre de Socio")
cuenta_mt5 = st.sidebar.text_input("Número de Cuenta MT5")
token_api = st.sidebar.text_input(
    "Token o Contraseña API", type="password"
)

if st.sidebar.button("Guardar Credenciales Seguras"):
  if socio_nombre and cuenta_mt5 and token_api:
    token_seguro = cifrar_dato(token_api)
    # Aquí es donde posteriormente guardaremos 'token_seguro' en tu base de datos
    st.sidebar.success(
        f"¡Credenciales cifradas para {socio_nombre} guardadas con éxito! 🔒"
    )
  else:
    st.sidebar.warning(
        "Por favor completa todos los campos para guardar de forma segura."
    )

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.subheader("📊 Monitoreo y Zonas de Liquidez")
st.info(
    "Aplicación corriendo en la nube de Streamlit. Utiliza el menú lateral"
    " para registrar y cifrar tus credenciales de acceso."
)

# Simulación de visualización de mercado
col1, col2, col3 = st.columns(3)
with col1:
  st.metric(label="Oro (XAU/USD)", value="$2,680.50", delta="+12.40")
with col2:
  st.metric(label="Estado del Servidor Cloud", value="Activo 🟢", delta="Online")
with col3:
  st.metric(label="Seguridad Activa", value="Cifrado Fernet 🔒", delta="Protegido")
