import streamlit as st
from supabase import create_client
from src.services.csv_service import convertir_preguntas_a_csv
from src.services.examen_service import calculate_exam_result, persist_exam_result
from src.utils.session_manager import ensure_defaults, reset_exam_state
from src.views.components.pregunta_form import renderizar_formulario_edicion_pregunta
from src.views.screens.admin_preguntas import render_admin_preguntas_screens
from src.views.screens.biblioteca import render_biblioteca_screen
from src.views.screens.examen_runtime import render_examen_runtime
from src.views.screens.examenes import render_examenes_screen
from src.views.screens.importacion import get_modal_importar_csv, get_modal_importar_pdf
from src.views.screens.perfil import render_perfil_screen
from src.views.screens.progreso import render_progreso_screen
from src.utils.ui_config import init_page_config  # <--- IMPORTAMOS LA UTILIDAD

init_page_config()  # <--- CONFIGURAMOS LA PÁGINA

def mostrar_progreso():
    render_progreso_screen(supabase=supabase, user_id=st.session_state.user.id)

def guardar_resultado_examen(datos_test, respuestas_usuario, tipo):
    """
    datos_test: Lista de diccionarios con las preguntas del test
    respuestas_usuario: Diccionario con {indice: 'A/B/C'}
    """
    result = calculate_exam_result(
        datos_test,
        respuestas_usuario,
        user_id=st.session_state.user.id,
    )
    persist_exam_result(
        supabase=supabase,
        user_id=st.session_state.user.id,
        exam_type=tipo,
        result=result,
    )
    return result.nota, result.aciertos, result.fallos
    
def limpiar_estado_maestro():
    """
    Realiza un reseteo integral de la sesión. 
    Limpia variables de test, configuración, filtros e importación.
    """
    
    reset_exam_state(st.session_state)

def mostrar_examen(titulo, lista_preguntas):
    render_examen_runtime(
        titulo=titulo,
        lista_preguntas=lista_preguntas,
        guardar_resultado_examen=guardar_resultado_examen,
        limpiar_estado_maestro=limpiar_estado_maestro,
    )

# --- 2. CONEXIÓN A SUPABASE ---
# Asegúrate de tener estos nombres exactos en tus Secrets de Streamlit
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_SERVICE_KEY"]
supabase = create_client(url, key)

session = supabase.auth.get_session()
if session and not st.session_state.user:
    st.session_state.user = session.user
    # Aquí podrías llamar a tu lógica de 'profiles' para obtener el rol
    st.session_state.sub_pantalla = "stats"

# --- 3. CARGA DE CSS ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- 4. INICIALIZACIÓN DE ESTADOS (SESSION STATE) ---
ensure_defaults(st.session_state)

def cambiar_vista(sub):
    st.session_state.sub_pantalla = sub
    st.session_state.p_seleccionada = None

def navegar_a(sub):
    limpiar_estado_maestro()
    cambiar_vista(sub)
    st.rerun()

modal_importar_pdf = get_modal_importar_pdf()
modal_importar = get_modal_importar_csv()


# --- 5. LÓGICA DE NAVEGACIÓN LATERAL (SIDEBAR) ---
# Solo mostramos el sidebar si el usuario está logueado
if st.session_state.user:
    with st.sidebar:
        # Intentamos sacar el nombre del perfil
        try:
            res_p = supabase.table("profiles").select("nombre").eq("id", st.session_state.user.id).single().execute()
            nombre_db = res_p.data.get("nombre")
        except:
            nombre_db = None

        st.markdown('<p class="titulo-pantalla" style="font-size: 28px; text-align: left;">OpoPMM 🏆</p>', unsafe_allow_html=True)
        
        # Lógica de saludo: Si hay nombre lo pone, si no, solo Hola
        saludo = f"¡Hola, **{nombre_db}**!" if nombre_db else "¡Hola!"
        st.write(saludo)
        st.divider()
        if st.button("📊 PROGRESO", width='stretch'):navegar_a("stats")
        if st.button("👤 MI PERFIL", width='stretch'):navegar_a("perfil")
        if st.button("📚 BIBLIOTECA DE LEYES", width='stretch'):navegar_a("biblioteca")
        if st.button("📝 REALIZAR TEST", width='stretch'):navegar_a("seleccion_tema")
        # 5. Gestión Preguntas (Solo ADMIN)
        if st.session_state.user_role == "admin":
            st.write("")
            st.markdown('<p style="font-size: 11px; opacity: 0.6; margin-left: 5px; letter-spacing: 1px;">ADMINISTRACIÓN</p>', unsafe_allow_html=True)
            if st.button("⚙️ GESTIÓN PREGUNTAS", width='stretch'):navegar_a("admin_preguntas")
        # 6. Cerrar Sesión (al final)
        st.write("###")
        if st.button("🚪 CERRAR SESIÓN", width='stretch'):
            supabase.auth.sign_out()
            st.session_state.clear()
            st.rerun()

# --- 6. PANTALLAS PRINCIPALES ---

# --- PANTALLA: INICIO (PÚBLICA) ---
if st.session_state.sub_pantalla == "inicio":
    st.markdown(f'<div class="titulo-pantalla">OpoPMM</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("---")
        if st.button("¡VAMOS A POR LA PLAZA!", width='stretch', type="primary"):
            cambiar_vista("login")
            st.rerun()

# --- PANTALLA: LOGIN / REGISTRO ---
elif st.session_state.sub_pantalla == "login":
    st.markdown(f'<div class="titulo-pantalla">ACCESO</div>', unsafe_allow_html=True)
    
    # Botón de Google (Fuera o dentro de los tabs)
    if st.button("🚀 ENTRAR CON GOOGLE", width='stretch'):
        from src.services.auth_service import iniciar_login_google
        auth_url = iniciar_login_google(supabase)
        # Redirección de JavaScript para abrir OAuth
        st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)

    tabs = st.tabs(["Entrar", "Registrarse"])
    
    with tabs[0]:
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Contraseña", type="password", key="login_pw")
        if st.button("INICIAR SESIÓN", width='stretch', type="primary"):
            try:
                # 1. Intentamos el login
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                
                # Verificamos que tenemos usuario antes de seguir
                if res.user:
                    st.session_state.user = res.user
                    
                    # 2. Consultar rol - Usamos el ID directamente del objeto 'res.user'
                    # Añadimos un pequeño manejo de error específico para el perfil
                    try:
                        p = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                        st.session_state.user_role = p.data['role'] if p.data else "regular"
                    except Exception as e:
                        # Si falla el perfil pero el login es ok, asignamos rol por defecto
                        st.session_state.user_role = "regular"
                    
                    # 3. CAMBIO DE VISTA Y REFRESCO
                    cambiar_vista("stats")
                    st.rerun()
                else:
                    st.error("No se pudo recuperar la información del usuario.")
                    
            except Exception as e:
                # Capturamos el error real para no confundir al usuario
                # Si el error es de Supabase por credenciales, saldrá aquí
                st.error("Error de acceso: Revisa tus credenciales.")

    with tabs[1]:
        n_email = st.text_input("Nuevo Email", key="reg_email")
        n_pw = st.text_input("Nueva Contraseña", type="password", key="reg_pw")
        if st.button("CREAR CUENTA", width='stretch'):
            try:
                # Si tienes la confirmación desactivada en Supabase, entra directo
                res = supabase.auth.sign_up({"email": n_email, "password": n_pw})
                st.success("¡Cuenta creada! Intenta loguearte ahora.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- PANTALLA: ESTADÍSTICAS ---
elif st.session_state.sub_pantalla == "stats":
    mostrar_progreso()

elif render_perfil_screen(supabase=supabase):
    pass

elif render_biblioteca_screen(
    supabase=supabase,
    limpiar_estado_maestro=limpiar_estado_maestro,
    cambiar_vista=cambiar_vista,
):
    pass

elif render_examenes_screen(
    supabase=supabase,
    mostrar_examen=mostrar_examen,
    navegar_a=navegar_a,
):
    pass

elif render_admin_preguntas_screens(
    supabase=supabase,
    renderizar_formulario_edicion=renderizar_formulario_edicion_pregunta,
    modal_importar_pdf=modal_importar_pdf,
    modal_importar=modal_importar,
    limpiar_estado_maestro=limpiar_estado_maestro,
    convertir_a_csv=convertir_preguntas_a_csv,
):
    pass
