import streamlit as st

def aplicar_estilo_amigable():
    estilo_css = """
    <style>
    /* Importar la fuente Poppins desde Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap');

    /* Aplicar la fuente a todos los elementos de la aplicación */
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Poppins', sans-serif !important;
    }
    
    /* Suavizar un poco el color del texto para que no sea negro puro (menos agresivo) */
    p, span, div {
        color: #333333; 
    }
    </style>
    """
    st.markdown(estilo_css, unsafe_allow_html=True)

# Llama a esta función al inicio de tu script
aplicar_estilo_amigable()

# El resto del código de tu bot...
st.title("Radar Liquidity Gold Bot")
st.write("Bienvenido a tu panel de control.")
