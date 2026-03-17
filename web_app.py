import streamlit as st
from supabase import create_client
import random
import os

# --- 1. CONFIGURACIÓN INICIAL Y CONEXIÓN ---
st.set_page_config(page_title="OpoPMM - Tu Plaza es Nuestra", layout="wide")

# Inicializar Supabase (Asegúrate de tener tus secrets configurados)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# Cargar CSS Externo
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- 2. GESTIÓN DE ESTADO (SESSION STATE) ---
if "sub_pantalla" not in st.session_state:
    st.session_state.sub_pantalla = "inicio"
if "user" not in st.session_state:
    st.session_state.user = None
if "user_role" not in st.session_state:
    st.session_state.user_role = "invitado"
if "temas_seleccionados" not in st.session_state:
    st.session_state.temas_seleccionados = []
if "examen_iniciado" not in st.session_state:
    st.session_state.examen_iniciado = "NO"

def cambiar_vista(sub):
    st.session_state.sub_pantalla = sub

# --- 3. FUNCIONES DE APOYO ---

def iniciar_examen(ids_temas, num_preguntas):
    """Carga las preguntas de los temas seleccionados e inicia el test"""
    res = supabase.table("preguntas").select("*").in_("tema_id", ids_temas).execute()
    if res.data:
        # Mezcla aleatoria y selección del número pedido
        preguntas = random.sample(res.data, min(len(res.data), num_preguntas))
        st.session_state.preguntas_examen = preguntas
        st.session_state.indice_pregunta = 0
        st.session_state.examen_iniciado = "SI"
        st.session_state.respuestas_usuario = {}
        st.session_state.resultado_final = None

# --- 4. LÓGICA DE NAVEGACIÓN (PANTALLAS) ---

# --- FLUJO DE EXAMEN ACTIVO ---
if st.session_state.examen_iniciado == "SI":
    # Aquí iría tu lógica de 'mostrar_pregunta()' 
    # Usando Comic Neue para el texto de la pregunta
    st.write("### Examen en curso...")
    if st.button("Finalizar Test"):
        st.session_state.examen_iniciado = "NO"
        st.rerun()

# --- FLUJO DE NAVEGACIÓN POR MENÚS ---
elif st.session_state.sub_pantalla == "inicio":
    st.markdown('<p class="titulo-pantalla">OpoPMM 🏆</p>', unsafe_allow_html=True)
    st.write("---")
    if st.button("¡VAMOS A POR LA PLAZA!", use_container_width=True, type="primary"):
        if st.session_state.user is None:
            cambiar_vista("login")
        else:
            cambiar_vista("menu_principal")
        st.rerun()

elif st.session_state.sub_pantalla == "login":
    st.markdown('<p class="titulo-pantalla">ACCESO</p>', unsafe_allow_html=True)
    tabs = st.tabs(["Entrar", "Registrarse"])
    
    with tabs[0]:
        email = st.text_input("Email", key="l_email")
        pw = st.text_input("Contraseña", type="password", key="l_pw")
        if st.button("INICIAR SESIÓN", use_container_width=True, type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                st.session_state.user = res.user
                # Consultar Rol en tabla profiles
                perfil = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                st.session_state.user_role = perfil.data['role']
                cambiar_vista("menu_principal")
                st.rerun()
            except:
                st.error("Credenciales incorrectas")

    with tabs[1]:
        n_email = st.text_input("Email", key="r_email")
        n_pw = st.text_input("Contraseña", type="password", key="r_pw")
        if st.button("CREAR MI CUENTA", use_container_width=True):
            try:
                supabase.auth.sign_up({"email": n_email, "password": n_pw})
                st.info("Revisa tu email para confirmar la cuenta.")
            except Exception as e:
                st.error(f"Error: {e}")

elif st.session_state.sub_pantalla == "menu_principal":
    st.markdown('<p class="titulo-pantalla">MENÚ PRINCIPAL</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 EXÁMENES", use_container_width=True):
            cambiar_vista("seleccion_tema")
            st.rerun()
        if st.button("📚 BIBLIOTECA", use_container_width=True):
            cambiar_vista("biblioteca")
            st.rerun()
    with c2:
        if st.button("📊 PROGRESO", use_container_width=True):
            cambiar_vista("stats")
            st.rerun()
        if st.button("👤 PERFIL", use_container_width=True):
            cambiar_vista("perfil")
            st.rerun()

    if st.session_state.user_role == "admin":
        st.divider()
        if st.button("🛠️ PANEL ADMINISTRADOR", use_container_width=True):
            cambiar_vista("panel_admin")
            st.rerun()
    
    if st.sidebar.button("Cerrar Sesión"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.user_role = "invitado"
        cambiar_vista("inicio")
        st.rerun()

elif st.session_state.sub_pantalla == "seleccion_tema":
    st.markdown('<p class="titulo-pantalla">TEMARIO</p>', unsafe_allow_html=True)
    
    if st.button("⬅️ VOLVER"): cambiar_vista("menu_principal"); st.rerun()

    res_t = supabase.table("temas").select("*").neq("id", 1).order("id").execute()
    if res_t.data:
        temas = res_t.data
        mitad = (len(temas) + 1) // 2
        col1, col2 = st.columns(2)
        
        for i, t in enumerate(temas):
            with (col1 if i < mitad else col2):
                sel = t['id'] in st.session_state.temas_seleccionados
                label = f"✅ {t['nombre']}" if sel else t['nombre']
                if st.button(label, key=f"t_{t['id']}", use_container_width=True, 
                             type="primary" if sel else "secondary"):
                    if sel: st.session_state.temas_seleccionados.remove(t['id'])
                    else: st.session_state.temas_seleccionados.append(t['id'])
                    st.rerun()

    if st.session_state.temas_seleccionados:
        st.divider()
        if st.button(f"🚀 CONFIGURAR EXAMEN ({len(st.session_state.temas_seleccionados)} TEMAS)", use_container_width=True):
            st.session_state.tema_elegido_id = st.session_state.temas_seleccionados
            cambiar_vista("config_examen")
            st.rerun()

elif st.session_state.sub_pantalla == "config_examen":
    st.markdown('<p class="titulo-pantalla">AJUSTES</p>', unsafe_allow_html=True)
    
    num = st.select_slider("Número de preguntas:", options=[10, 20, 40, 60, 100], value=20)
    
    if st.button("🚀 EMPEZAR TEST", use_container_width=True, type="primary"):
        ids = st.session_state.tema_elegido_id
        lista_ids = ids if isinstance(ids, list) else [ids]
        
        iniciar_examen(lista_ids, num)
        # Limpiamos selección de botones para la vuelta
        st.session_state.temas_seleccionados = []
        st.rerun()
    
    if st.button("CANCELAR"): cambiar_vista("seleccion_tema"); st.rerun()

# --- PANTALLAS EN DESARROLLO (STUBS) ---
elif st.session_state.sub_pantalla in ["biblioteca", "stats", "perfil", "panel_admin"]:
    st.markdown(f'<p class="titulo-pantalla">{st.session_state.sub_pantalla.upper()}</p>', unsafe_allow_html=True)
    st.warning("Sección en construcción...")
    if st.button("VOLVER AL MENÚ"): cambiar_vista("menu_principal"); st.rerun()
