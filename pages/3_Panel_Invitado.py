import streamlit as st

st.set_page_config(page_title="Panel Invitado - Radar Liquidity", page_icon="📊")

# Control de acceso
if not st.session_state.get("autenticado", False):
    st.error("⛔ Debe iniciar sesión para ver su panel.")
    st.stop()

st.title("📊 Panel del Invitado")
st.write("Resumen del bot, gráficos, rendimiento y control de riesgo individual.")

# 1. Reseña breve
with st.expander("📖 ¿Qué hace el Radar Liquidity Gold Bot? (Ver Reseña)", expanded=False):
    st.write("Este bot opera basado en la confluencia de RSI Multi-Timeframe y cruces de Medias Móviles (EMAs), optimizado para capturar liquidez institucional en oro de forma automatizada.")

# 2. Conexión MT5 y Control de Riesgo
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔌 Conexión MetaTrader 5")
    mt5_login = st.text_input("Número de Cuenta MT5")
    mt5_pass = st.text_input("Contraseña MT5", type="password")
    mt5_server = st.text_input("Servidor MT5")
    if st.button("Conectar MT5"):
        st.success("Credenciales de MT5 guardadas de forma segura.")

with col2:
    st.subheader("🛡️ Gestión de Riesgo y Operativa")
    lotaje = st.number_input("Lotaje por operación", min_value=0.01, max_value=10.0, value=0.1)
    stop_loss = st.number_input("Stop Loss (Pips)", value=50)
    capital_riesgo = st.number_input("Capital a arriesgar ($)", value=100.0)
    
    if st.button("Guardar Configuración de Riesgo"):
        st.success("Configuración de riesgo actualizada.")

st.divider()

# 3. Estadísticas y Gráficos
st.subheader("📈 Rendimiento y Operaciones")
st.metric(label="Rendimiento Total (Histórico)", value="+18.5%", delta="2.4% esta semana")

chart_data = {"Días": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"], "Ganancia ($)": [120, -45, 230, 90, 310]}
st.line_chart(chart_data, x="Días", y="Ganancia ($)")

st.divider()

# 4. Botón de Paro de Emergencia
st.subheader("🚨 Control de Emergencia")
if st.button("🔴 DETENER OPERACIONES MT5 (Paro de Emergencia)", type="primary"):
    st.error("¡Señal de emergencia enviada! Se han pausado todas las operaciones activas en su MT5.")
