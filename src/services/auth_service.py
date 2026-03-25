from supabase import Client

def iniciar_login_google(supabase: Client):
    """
    Genera la URL de autenticación de Google y redirige al usuario.
    """
    # En local suele ser http://localhost:8501
    # En producción debe ser la URL de tu app en Streamlit Cloud
    #redirect_url = "http://localhost:8501" 
    redirect_url = "https://opopmm.streamlit.app"
    
    res = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {
            "redirect_to": redirect_url
        }
    })
    return res.url