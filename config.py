import streamlit as st
from typing import Tuple


class Config:
    """Configuración centralizada de la aplicación OpoPMM."""

    PAGE_TITLE = "OpoPMM - Tu Plaza es Nuestra"
    PAGE_LAYOUT = "wide"

    ROLES = {
        "admin": "admin",
        "regular": "regular",
        "invitado": "invitado",
    }

    EXAM_MODES = {
        "ingles": "ingles",
        "por_temas": "por_temas",
        "simulacro": "simulacro",
    }

    QUESTION_LIMITS = [10, 20, 40, 80, 100]
    DEFAULT_QUESTION_LIMIT = 20

    NOTA_FACTOR = 0.33

    @staticmethod
    def get_supabase_credentials() -> Tuple[str, str]:
        """Obtiene credenciales de Supabase de forma segura desde secrets."""
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_SERVICE_KEY"]
            if not url or not key:
                raise ValueError("Credenciales vacías en secrets")
            return url, key
        except KeyError as e:
            st.error(f"❌ Falta configurar en secrets: {str(e)}")
            st.stop()
        except Exception as e:
            st.error(f"❌ Error al cargar credenciales: {str(e)}")
            st.stop()
