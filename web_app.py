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


def mostrar_progreso():
    render_progreso_screen(supabase=supabase, user_id=st.session_state.user.id)
    if st.button("⬅️ VOLVER AL MENÚ"):
        navegar_a("menu_principal")


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
    """Resetea estado de examen/importación sin tocar auth."""
    reset_exam_state(st.session_state)


def mostrar_examen(titulo, lista_preguntas):
    render_examen_runtime(
        titulo=titulo,
        lista_preguntas=lista_preguntas,
        guardar_resultado_examen=guardar_resultado_examen,
        limpiar_estado_maestro=limpiar_estado_maestro,
    )


# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="OpoPMM - Tu Plaza es Nuestra",
    layout="wide",
    initial_sidebar_state="auto",
)

# --- 2. CONEXIÓN A SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_SERVICE_KEY"]
supabase = create_client(url, key)

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


def _nombre_perfil_sidebar():
    try:
        res = (
            supabase.table("profiles")
            .select("nombre")
            .eq("id", st.session_state.user.id)
            .single()
            .execute()
        )
        return res.data.get("nombre") if res.data else None
    except Exception:
        return None


def _pantallas_tras_menu():
    """Enruta stats, perfil, biblioteca, exámenes y admin (una sola pantalla por ejecución)."""
    if st.session_state.sub_pantalla == "stats":
        mostrar_progreso()
        return True
    if render_perfil_screen(supabase=supabase):
        return True
    if render_biblioteca_screen(
        supabase=supabase,
        limpiar_estado_maestro=limpiar_estado_maestro,
        cambiar_vista=cambiar_vista,
    ):
        return True
    if render_examenes_screen(
        supabase=supabase,
        mostrar_examen=mostrar_examen,
        navegar_a=navegar_a,
    ):
        return True
    if render_admin_preguntas_screens(
        supabase=supabase,
        renderizar_formulario_edicion=renderizar_formulario_edicion_pregunta,
        modal_importar_pdf=modal_importar_pdf,
        modal_importar=modal_importar,
        limpiar_estado_maestro=limpiar_estado_maestro,
        convertir_a_csv=convertir_preguntas_a_csv,
    ):
        return True
    return False


modal_importar_pdf = get_modal_importar_pdf()
modal_importar = get_modal_importar_csv()


# --- 5. LÓGICA DE NAVEGACIÓN LATERAL (SIDEBAR) ---
if st.session_state.user:
    with st.sidebar:
        nombre_db = _nombre_perfil_sidebar()

        st.markdown(
            '<p class="titulo-pantalla" style="font-size: 28px; text-align: left;">OpoPMM 🏆</p>',
            unsafe_allow_html=True,
        )

        saludo = f"¡Hola, **{nombre_db}**!" if nombre_db else "¡Hola!"
        st.write(saludo)
        st.divider()
        if st.button("📊 PROGRESO", use_container_width=True):
            navegar_a("stats")
        if st.button("👤 MI PERFIL", use_container_width=True):
            navegar_a("perfil")
        if st.button("📚 BIBLIOTECA DE LEYES", use_container_width=True):
            navegar_a("biblioteca")
        if st.button("📝 REALIZAR TEST", use_container_width=True):
            navegar_a("seleccion_tema")
        if st.session_state.user_role == "admin":
            st.write("")
            st.markdown(
                '<p style="font-size: 11px; opacity: 0.6; margin-left: 5px; letter-spacing: 1px;">ADMINISTRACIÓN</p>',
                unsafe_allow_html=True,
            )
            if st.button("⚙️ GESTIÓN PREGUNTAS", use_container_width=True):
                navegar_a("admin_preguntas")
        st.write("###")
        if st.button("🚪 CERRAR SESIÓN", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.clear()
            st.rerun()

# --- 6. PANTALLAS PRINCIPALES ---

if st.session_state.sub_pantalla == "inicio":
    st.markdown('<div class="titulo-pantalla">OpoPMM</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("---")
        if st.button("¡VAMOS A POR LA PLAZA!", use_container_width=True, type="primary"):
            cambiar_vista("login")
            st.rerun()

elif st.session_state.sub_pantalla == "login":
    st.markdown('<div class="titulo-pantalla">ACCESO</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Entrar", "Registrarse"])

    with tabs[0]:
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Contraseña", type="password", key="login_pw")
        if st.button("INICIAR SESIÓN", use_container_width=True, type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                if res.user:
                    st.session_state.user = res.user
                    try:
                        p = (
                            supabase.table("profiles")
                            .select("role")
                            .eq("id", res.user.id)
                            .single()
                            .execute()
                        )
                        st.session_state.user_role = p.data["role"] if p.data else "regular"
                    except Exception:
                        st.session_state.user_role = "regular"
                    cambiar_vista("menu_principal")
                    st.rerun()
                else:
                    st.error("No se pudo recuperar la información del usuario.")
            except Exception:
                st.error("Error de acceso: Revisa tus credenciales.")

    with tabs[1]:
        n_email = st.text_input("Nuevo Email", key="reg_email")
        n_pw = st.text_input("Nueva Contraseña", type="password", key="reg_pw")
        if st.button("CREAR CUENTA", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": n_email, "password": n_pw})
                st.success("¡Cuenta creada! Intenta loguearte ahora.")
            except Exception as e:
                st.error(f"Error: {e}")

elif st.session_state.sub_pantalla == "menu_principal":
    st.markdown('<div class="titulo-pantalla">CENTRO DE CONTROL</div>', unsafe_allow_html=True)
    st.info("Bienvenido. Utiliza el menú de la izquierda para navegar por la aplicación.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Nota Media", "7.2", "0.5")
    c2.metric("Test Completados", "24")
    c3.metric("Días para Examen", "124")

elif _pantallas_tras_menu():
    pass
