# Panel Lateral: Registro Automático
st.sidebar.header("🚀 Conectar Nueva Cuenta MT5")
socio_nombre = st.sidebar.text_input("Nombre de Socio")
mt5_login = st.sidebar.text_input("Número de Cuenta (Login)")
mt5_password = st.sidebar.text_input("Contraseña de Trading", type="password")

# Desplegable ampliado con servidores de MetaTrader oficiales, Vantage y más
opciones_brokers = [
    "Selecciona o escribe...",
    # MetaTrader / MetaQuotes Oficiales
    "MetaQuotes-Demo",
    # Vantage International
    "VantageInternational-Live 01",
    "VantageInternational-Live 02",
    "VantageInternational-Live 03",
    "VantageInternational-Live 04",
    "VantageInternational-Demo",
    # Exness
    "Exness-Real11",
    "Exness-Real12",
    "Exness-Real13",
    "Exness-Trial",
    # RoboForex
    "RoboForex-Pro",
    "RoboForex-ECN",
    "RoboForex-Demo",
    # IC Markets
    "ICMarketsSC-Live 01",
    "ICMarketsSC-Live 02",
    "ICMarketsSC-Demo",
    # Otro manual
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
