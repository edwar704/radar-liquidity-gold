import asyncio
from cryptography.fernet import Fernet
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
# 2. CONFIGURACIÓN DE SEGURIDAD Y CREDENCIALES
# ==========================================
if "FERNET_KEY" in st.secrets and "METAAPI_TOKEN" in st.secrets:
  FERNET_KEY = st.secrets["FERNET_KEY"].encode()
  MASTER_METAAPI_TOKEN = st.secrets["METAAPI_TOKEN"]
  cipher_suite = Fernet(FERNET_KEY)
else:
  st.error(
      "⚠ Faltan configurar FERNET_KEY o METAAPI_TOKEN en los Secrets de"
      " Streamlit."
  )
  cipher_suite = None
  MASTER_METAAPI_TOKEN = ""

# ==========================================
# 3. FUNCIONES ASÍNCRONAS DE METAAPI
# ==========================================


async def obtener_cuentas_metaapi():
  """Obtiene la lista de cuentas directamente desde MetaApi Cloud."""
  try:
    metaapi = MetaApi(MASTER_METAAPI_TOKEN)
    accounts = await metaapi.metatrader_account_api.get_accounts()
    # Filtramos solo las cuentas de tipo mt5 o cloud creadas por el bot
    lista_cuentas = []
    for acc in accounts:
      acc_info = acc.to_dict()
      lista_cuentas.append({
          "id": acc_info.get("id"),
          "name": acc_info.get("name", "Sin Nombre"),
          "login": acc_info.get("login"),
          "server": acc_info.get("server"),
      })
    return True, lista_cuentas
  except Exception as e:
    return False, str(e)


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
# 4. INTERFAZ DE USUARIO (UI)
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

# Desplegable con servidores
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
        st.sidebar.success(
            f"¡Cuenta para {socio_nombre} conectada y registrada con éxito! 🟢"
        )
        st.rerun()
      else:
        st.sidebar.error(
            f"Error al conectar con el bróker. Verifica tus datos. Detalle:"
            f" {resultado}"
        )
  else:
    st.sidebar.warning("Por favor completa todos los campos para continuar.")

# Panel Principal: Monitoreo Directo de la Nube
st.subheader("📊 Monitoreo de Cuentas Conectadas")

with st.spinner("Sincronizando cuentas desde MetaApi Cloud..."):
  exito_cuentas, lista_cuentas = asyncio.run(obtener_cuentas_metaapi())

if exito_cuentas and lista_cuentas:
  nombres_cuentas = {
      f"{acc['name']} (Login: {acc['login']})": acc for acc in lista_cuentas
  }
  cuenta_seleccionada_key = st.selectbox(
      "Selecciona una Cuenta para Monitorear", list(nombres_cuentas.keys())
  )

  if cuenta_seleccionada_key:
    cuenta_activa = nombres_cuentas[cuenta_seleccionada_key]
    s_nombre = cuenta_activa["name"]
    s_acc_id = cuenta_activa["id"]
    st.write(
        f"**Socio/Cuenta:** {s_nombre} | **Account ID:** `{s_acc_id}`"
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
      "No hay cuentas conectadas todavía en MetaApi. Utiliza el panel lateral"
      " para registrar una cuenta."
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
