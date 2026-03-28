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

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(
    page_title="OpoPMM - Tu Plaza es Nuestra",
    layout="wide",
    initial_sidebar_state="collapsed", # Sidebar cerrado para favorecer los Tabs
)

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_SERVICE_KEY"]
supabase = create_client(url, key)

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

ensure_defaults(st.session_state)

# --- 2. FUNCIONES DE APOYO ---
def cambiar_vista(sub):
    st.session_state.sub_pantalla = sub
    st.session_state.p_seleccionada = None

def navegar_a(sub):
    limpiar_estado_maestro()
    cambiar_vista(sub)
    st.rerun()

def limpiar_estado_maestro():
    reset_exam_state(st.session_state)

def guardar_resultado_examen(datos_test, respuestas_usuario, tipo):
    result = calculate_exam_result(datos_test, respuestas_usuario, user_id=st.session_state.user.id)
    ids_ordenados = [p.get("id") for p in datos_test]
    persist_exam_result(
        supabase=supabase,
        user_id=st.session_state.user.id,
        exam_type=tipo,
        result=result,
        preguntas_ids=ids_ordenados,
        respuestas_usuario=respuestas_usuario,
    )
    return result.nota, result.aciertos, result.fallos

def mostrar_examen(titulo, lista_preguntas):
    # Cuando iniciamos un examen, cambiamos la vista para que desaparezcan los Tabs
    st.session_state.preguntas_examen = lista_preguntas
    st.session_state.titulo_examen_actual = titulo
    cambiar_vista("examen_runtime")
    st.rerun()

# --- 3. COMPONENTES GLOBALES ---
modal_importar_pdf = get_modal_importar_pdf()
modal_importar = get_modal_importar_csv()

# --- 4. LÓGICA DE NAVEGACIÓN ---

# A. FLUJO PARA USUARIOS LOGUEADOS
if st.session_state.user:
    
    # --- MODO EXAMEN (Sin Tabs para evitar distracciones/errores) ---
    if st.session_state.sub_pantalla == "examen_runtime":
        render_examen_runtime(
            titulo=st.session_state.get("titulo_examen_actual", "EXAMEN"),
            lista_preguntas=st.session_state.preguntas_examen,
            guardar_resultado_examen=guardar_resultado_examen,
            limpiar_estado_maestro=limpiar_estado_maestro,
        )
    
    elif st.session_state.sub_pantalla == "repaso_historial":
        render_examen_runtime(
            titulo="REPASO DE EXAMEN",
            lista_preguntas=st.session_state.preguntas_examen,
            guardar_resultado_examen=guardar_resultado_examen,
            limpiar_estado_maestro=limpiar_estado_maestro,
        )

    # --- MODO APP NORMAL (Navegación por Tabs) ---
    else:
        st.markdown("""
            <style>
            .stTabs [data-baseweb="tab-list"] { gap: 8px; justify-content: space-around; }
            .stTabs [data-baseweb="tab"] { font-size: 12px; padding: 10px 5px; }
            </style>
        """, unsafe_allow_html=True)

        titulos_tabs = ["📊", "👤", "📚", "📝", "📜"]
        if st.session_state.user_role == "admin":
            titulos_tabs.append("⚙️")
        titulos_tabs.append("🚪")

        tabs = st.tabs(titulos_tabs)

        with tabs[0]: # PROGRESO
            render_progreso_screen(supabase=supabase, user_id=st.session_state.user.id)
        
        with tabs[1]: # PERFIL
            render_perfil_screen(supabase=supabase)

        with tabs[2]: # BIBLIOTECA
            render_biblioteca_screen(
                supabase=supabase,
                limpiar_estado_maestro=limpiar_estado_maestro,
                cambiar_vista=cambiar_vista
            )

        with tabs[3]: # TESTS
            render_examenes_screen(
                supabase=supabase,
                mostrar_examen=mostrar_examen,
                navegar_a=navegar_a
            )

        with tabs[4]: # HISTORIAL
            from src.views.screens.historial import render_historial_screen
            render_historial_screen(supabase)

        idx_dinamico = 5
        if st.session_state.user_role == "admin":
            with tabs[idx_dinamico]:
                render_admin_preguntas_screens(
                    supabase=supabase,
                    renderizar_formulario_edicion=renderizar_formulario_edicion_pregunta,
                    modal_importar_pdf=modal_importar_pdf,
                    modal_importar=modal_importar,
                    limpiar_estado_maestro=limpiar_estado_maestro,
                    convertir_a_csv=convertir_preguntas_a_csv,
                )
            idx_dinamico += 1

        with tabs[idx_dinamico]: # SALIR
            st.warning("¿Quieres cerrar la sesión?")
            if st.button("CONFIRMAR CIERRE", use_container_width=True, type="primary"):
                supabase.auth.sign_out()
                st.session_state.clear()
                st.rerun()

# B. FLUJO PARA USUARIOS NO LOGUEADOS (Login/Registro)
else:
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
        t_login, t_reg = st.tabs(["Entrar", "Registrarse"])

        with t_login:
            email = st.text_input("Email", key="login_email")
            pw = st.text_input("Contraseña", type="password", key="login_pw")
            if st.button("INICIAR SESIÓN", use_container_width=True, type="primary"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                    if res.user:
                        st.session_state.user = res.user
                        p = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                        st.session_state.user_role = p.data["role"] if p.data else "regular"
                        cambiar_vista("stats")
                        st.rerun()
                except Exception:
                    st.error("Credenciales incorrectas")

        with t_reg:
            n_email = st.text_input("Nuevo Email", key="reg_email")
            n_pw = st.text_input("Nueva Contraseña", type="password", key="reg_pw")
            if st.button("CREAR CUENTA", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": n_email, "password": n_pw})
                    st.success("Cuenta creada. ¡Ya puedes entrar!")
                except Exception as e:
                    st.error(f"Error: {e}")