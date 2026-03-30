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
    page_icon="assets/logo.png",  # <--- Ruta actualizada
    layout="wide",
    initial_sidebar_state="collapsed", # Sidebar cerrado para favorecer los Tabs
)

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_SERVICE_KEY"]
supabase = create_client(url, key)

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

ensure_defaults(st.session_state)

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
        # 1. Definimos qué pestañas verá todo el mundo
        titulos_tabs = ["📊", "👤", "📝", "📜"] # Progreso, Perfil, Tests, Historial

        # 2. Lógica condicional para Admin / Biblioteca
        es_admin = st.session_state.get("user_role") == "admin"

        if es_admin:
            titulos_tabs.append("📚") # Biblioteca (solo admin)
            titulos_tabs.append("⚙️") # Gestión (solo admin)

        # 3. El botón de salir siempre va al final
        titulos_tabs.append("🚪")

        # 4. Creamos las pestañas
        tabs = st.tabs(titulos_tabs)

        # --- RENDERIZADO ASOCIADO A CADA ÍNDICE ---
        curr = 0

        with tabs[curr]: # 📊 PROGRESO
            render_progreso_screen(supabase=supabase, user_id=st.session_state.user.id)
        curr += 1

        with tabs[curr]: # 👤 PERFIL
            render_perfil_screen(supabase=supabase)
        curr += 1

        with tabs[curr]: # 📝 TESTS
            render_examenes_screen(supabase=supabase, mostrar_examen=mostrar_examen, navegar_a=navegar_a)
        curr += 1

        with tabs[curr]: # 📜 HISTORIAL
            from src.views.screens.historial import render_historial_screen
            render_historial_screen(supabase)
        curr += 1

        if es_admin:
            with tabs[curr]: # 📚 BIBLIOTECA
                render_biblioteca_screen(
                    supabase=supabase, 
                    limpiar_estado_maestro=limpiar_estado_maestro, 
                    cambiar_vista=cambiar_vista
                )
            curr += 1

            with tabs[curr]: # ⚙️ GESTIÓN
                render_admin_preguntas_screens(
                    supabase=supabase,
                    renderizar_formulario_edicion=renderizar_formulario_edicion_pregunta,
                    modal_importar_pdf=modal_importar_pdf,
                    modal_importar=modal_importar,
                    limpiar_estado_maestro=limpiar_estado_maestro,
                    convertir_a_csv=convertir_preguntas_a_csv,
                )
            curr += 1

        with tabs[curr]: # 🚪 SALIR
            st.warning("¿Quieres cerrar la sesión?")
            if st.button("CONFIRMAR CIERRE", use_container_width=True, type="primary"):
                supabase.auth.sign_out()
                st.session_state.clear()
                st.rerun()

# B. FLUJO PARA USUARIOS NO LOGUEADOS (Login/Registro)
else:
    # Forzamos una pantalla de bienvenida limpia si no hay sub_pantalla definida
    if st.session_state.sub_pantalla not in ["login", "registro"]:
        st.markdown('<div class="titulo-pantalla">OpoPMM</div>', unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; opacity: 0.8;'>Tu Plaza es Nuestra</h4>", unsafe_allow_html=True)
        
        st.write("###")
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            if st.button("🚀 ¡VAMOS A POR LA PLAZA!", use_container_width=True, type="primary"):
                cambiar_vista("login")
                st.rerun()
    
    else:
        # Usamos los nuevos Tabs con estilo emoji para Login/Registro
        st.markdown('<div class="titulo-pantalla">ACCESO AL SISTEMA</div>', unsafe_allow_html=True)
        
        # Sincronizamos el tab activo con la sub_pantalla
        tab_index = 0 if st.session_state.sub_pantalla == "login" else 1
        t_login, t_reg = st.tabs(["🔐", "📝"])

        with t_login:
            st.write("###")
            email = st.text_input("Email", key="login_email", placeholder="tu@email.com")
            pw = st.text_input("Contraseña", type="password", key="login_pw", placeholder="••••••••")
            
            if st.button("INICIAR SESIÓN", use_container_width=True, type="primary"):
                try:
                    with st.spinner("Verificando credenciales..."):
                        res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                        if res.user:
                            st.session_state.user = res.user
                            # Obtenemos el perfil para saber el rol
                            p = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                            st.session_state.user_role = p.data["role"] if p.data else "regular"
                            # Limpieza y redirección
                            st.session_state.sub_pantalla = "stats" # Vista por defecto al entrar
                            st.success("¡Bienvenido de nuevo!")
                            st.rerun()
                except Exception:
                    st.error("❌ Credenciales incorrectas o cuenta no verificada")
        with t_reg:
            st.write("###")
            st.info("Crea tu cuenta para guardar tu progreso y estadísticas.")
            n_email = st.text_input("Nuevo Email", key="reg_email", placeholder="ejemplo@email.com")
            n_pw = st.text_input("Nueva Contraseña", type="password", key="reg_pw", help="Mínimo 6 caracteres")
            if st.button("CREAR CUENTA", use_container_width=True):
                if len(n_pw) < 6:
                    st.warning("La contraseña debe tener al menos 6 caracteres")
                else:
                    try:
                        with st.spinner("Creando cuenta..."):
                            supabase.auth.sign_up({"email": n_email, "password": n_pw})
                            st.success("✅ ¡Cuenta creada con éxito!")
                            st.balloons()
                            st.info("Revisa tu email para confirmar la cuenta (si el envío está activo) y luego entra en el apartado 'Entrar'.")
                    except Exception as e:
                        st.error(f"Error al registrar: {str(e)}")