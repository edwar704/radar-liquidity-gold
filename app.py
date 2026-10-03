# ==========================================
  # PANEL LATERAL DE ADMINISTRADOR (Enlace fijo)
  # ==========================================
  if is_admin_user:
    st.sidebar.markdown("---")
    st.sidebar.header("🎫 Generador de Invitaciones")

    # Enlace base fijo directamente en el código
    url_base_bot = "https://radar-liquidity-gold-bot.streamlit.app"

    if st.sidebar.button("✨ Generar Nuevo Código"):
      nuevo_cod = generar_nuevo_codigo()
      enlace_con_parametro = f"{url_base_bot.strip('/')}/?invite={nuevo_cod}"

      st.sidebar.success("¡Código generado con éxito!")
      st.sidebar.markdown(
          "Copia este mensaje y envíaselo a tu socio de forma directa:"
      )
      st.sidebar.code(
          f"¡Hola! Regístrate en el bot haciendo clic aquí:\n{enlace_con_parametro}\n\nTu"
          f" código de invitación es: {nuevo_cod}",
          language="text",
      )
