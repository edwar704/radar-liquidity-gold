import streamlit as st
import pandas as pd

st.set_page_config(page_title="Monitoreo Bot - Radar Liquidity", page_icon="🤖")

st.title("🤖 Monitoreo y Ejecución del Bot")
st.write("Estado en tiempo real del algoritmo Radar Liquidity Gold Bot y señales emitidas.")

# Métricas en vivo del Bot
col1, col2, col3 = st.columns(3)
col1.metric("Estado del Mercado", "Alcista (GOLD)", "RSI > 50")
col2.metric("Última Señal", "COMPRA (BUY)", "Hace 5 min")
col3.metric("Conexiones Activas", "14 cuentas MT5", "Estable")

st.subheader("📋 Registro de Alertas y Webhooks Recientes")

df_signals = pd.DataFrame({
    "Hora": ["06:15:20", "05:40:12", "04:10:05"],
    "Símbolo": ["XAUUSD", "XAUUSD", "XAUUSD"],
    "Señal": ["BUY", "SELL", "BUY"],
    "RSI Status": ["Sobreventa", "Sobrecompra", "Neutral"],
    "Estado": ["Ejecutado", "Ejecutado", "Ejecutado"]
})
st.dataframe(df_signals, use_container_width=True)
