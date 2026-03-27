import streamlit as st
import os
from PIL import Image

def init_page_config():
    """
    Configura el favicon y el layout de la aplicación.
    Centraliza la gestión de assets estáticos.
    """
    current_dir = os.path.dirname(__file__)
    # Subimos dos niveles porque estamos en src/utils/ y assets está en la raíz
    path_logo = os.path.join(current_dir, "..", "..", "assets", "logo.png")

    try:
        img_logo = Image.open(path_logo)
    except Exception:
        img_logo = "🏆"

    st.set_page_config(
        page_title="OpoPMM - Tu Plaza es Nuestra",
        page_icon=img_logo,
        layout="wide",
        initial_sidebar_state="auto"
    )