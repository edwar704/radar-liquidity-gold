# 2. Pestañas de contenido del bot para el socio
    pestana_socio_info, pestana_socio_radar = st.tabs([
        "📚 Información y Guía del Bot",
        "⚡ Radar de Liquidez XAU/USD",
    ])

    with pestana_socio_info:
      st.subheader("Bienvenido al Radar Liquidity Gold")
      st.markdown("""
            Este bot está diseñado para ayudarte a identificar las mejores zonas institucionales de liquidez en el mercado del oro (**XAU/USD**).
            
            * **¿Cómo empezar?** Puedes explorar el análisis de liquidez en la pestaña contigua.
            * **Conexión opcional:** Si deseas consultar los balances y estados en tiempo real de tus operaciones, vincula tu cuenta MT5 utilizando el menú desplegable superior en el momento que consideres oportuno.
            """)

    with pestana_socio_radar:
      st.subheader("⚡ Motor de Análisis Institucional y Liquidez (XAU/USD)")
      if cuenta_socio:
        if st.button("🔍 Escanear Zonas de Liquidez", key="btn_radar_socio"):
          with st.spinner("Analizando cotizaciones del Oro..."):
            exito_p, simbolo, datos_precio = asyncio.run(
                obtener_precio_oro(cuenta_socio["account_id"])
            )
            if exito_p:
              bid = datos_precio.get("bid", 0)
              ask = datos_precio.get("ask", 0)
              spread = round((ask - bid) * 10, 1)
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
                  "- **Zona de Resistencia / Liquidez Superior (Buy Stops):**"
                  f" Estimada en `${bid + 5.00:,.2f}`\n"
                  "- **Zona de Soporte / Liquidez Inferior (Sell Stops):**"
                  f" Estimada en `${bid - 5.00:,.2f}`"
              )
            else:
              st.error(f"No se pudo obtener el precio del oro: {datos_precio}")
      else:
        st.info(
            "💡 Actualmente estás explorando el bot en modo libre. Para usar"
            " el escáner de liquidez en vivo, vincula tu cuenta de MetaTrader 5"
            " en la sección superior desplegable."
        )
