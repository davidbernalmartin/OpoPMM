import streamlit as st
from supabase import create_client
import random

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="OpoPMM - Tu Plaza es Nuestra",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- 2. CONEXIÓN A SUPABASE ---
# Asegúrate de tener estos nombres exactos en tus Secrets de Streamlit
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- 3. CARGA DE CSS ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- 4. INICIALIZACIÓN DE ESTADOS (SESSION STATE) ---
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
if "preguntas_simulacro" not in st.session_state:
    st.session_state.preguntas_simulacro = []
if "indice_pregunta" not in st.session_state:
    st.session_state.indice_pregunta = 0
if "respuestas_usuario" not in st.session_state:
    st.session_state.respuestas_usuario = {} # Guardaremos {indice: respuesta}
if "examen_finalizado" not in st.session_state:
    st.session_state.examen_finalizado = False

def cambiar_vista(sub):
    st.session_state.sub_pantalla = sub

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

        # 1. Estadísticas / Progreso
        if st.button("📊 PROGRESO", use_container_width=True):
            cambiar_vista("stats")
            st.rerun()

        # 2. Perfil
        if st.button("👤 MI PERFIL", use_container_width=True):
            cambiar_vista("perfil")
            st.rerun()

        # 3. Biblioteca de Leyes
        if st.button("📚 BIBLIOTECA DE LEYES", use_container_width=True):
            cambiar_vista("biblioteca")
            st.rerun()

        # 4. Exámenes
        if st.button("📝 REALIZAR TEST", use_container_width=True):
            cambiar_vista("seleccion_tema")
            st.rerun()

        # 5. Gestión Preguntas (Solo ADMIN)
        if st.session_state.user_role == "admin":
            st.write("")
            st.markdown('<p style="font-size: 11px; opacity: 0.6; margin-left: 5px; letter-spacing: 1px;">ADMINISTRACIÓN</p>', unsafe_allow_html=True)
            if st.button("⚙️ GESTIÓN PREGUNTAS", use_container_width=True):
                cambiar_vista("panel_admin")
                st.rerun()

        # 6. Cerrar Sesión (al final)
        st.write("###")
        if st.button("🚪 CERRAR SESIÓN", use_container_width=True, key="logout"):
            supabase.auth.sign_out()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# --- 6. PANTALLAS PRINCIPALES ---

# --- PANTALLA: INICIO (PÚBLICA) ---
if st.session_state.sub_pantalla == "inicio":
    st.markdown('<p class="titulo-pantalla">OpoPMM</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("---")
        if st.button("¡VAMOS A POR LA PLAZA!", use_container_width=True, type="primary"):
            cambiar_vista("login")
            st.rerun()

# --- PANTALLA: LOGIN / REGISTRO ---
elif st.session_state.sub_pantalla == "login":
    st.markdown('<p class="titulo-pantalla">ACCESO</p>', unsafe_allow_html=True)
    tabs = st.tabs(["Entrar", "Registrarse"])
    
    with tabs[0]:
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Contraseña", type="password", key="login_pw")
        if st.button("INICIAR SESIÓN", use_container_width=True, type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                st.session_state.user = res.user
                # Consultar rol
                p = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                st.session_state.user_role = p.data['role'] if p.data else "regular"
                cambiar_vista("menu_principal")
                st.rerun()
            except:
                st.error("Error de acceso: Revisa tus credenciales.")

    with tabs[1]:
        n_email = st.text_input("Nuevo Email", key="reg_email")
        n_pw = st.text_input("Nueva Contraseña", type="password", key="reg_pw")
        if st.button("CREAR CUENTA", use_container_width=True):
            try:
                # Si tienes la confirmación desactivada en Supabase, entra directo
                res = supabase.auth.sign_up({"email": n_email, "password": n_pw})
                st.success("¡Cuenta creada! Intenta loguearte ahora.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- PANTALLA: MENÚ PRINCIPAL (RESUMEN) ---
elif st.session_state.sub_pantalla == "menu_principal":
    st.markdown('<p class="titulo-pantalla">CENTRO DE CONTROL</p>', unsafe_allow_html=True)
    st.info("Bienvenido. Utiliza el menú de la izquierda para navegar por la aplicación.")
    
    # Dashboard rápido
    c1, c2, c3 = st.columns(3)
    c1.metric("Nota Media", "7.2", "0.5")
    c2.metric("Test Completados", "24")
    c3.metric("Días para Examen", "124")

# --- PANTALLA: ESTADÍSTICAS ---
elif st.session_state.sub_pantalla == "stats":
    st.markdown('<p class="titulo-pantalla">PROGRESO</p>', unsafe_allow_html=True)
    st.write("Aquí verás tus gráficos de evolución por temas.")

# --- PANTALLA: PERFIL ---
elif st.session_state.sub_pantalla == "perfil":
    st.markdown('<p class="titulo-pantalla">MI PERFIL</p>', unsafe_allow_html=True)
    
    # 1. Recuperar datos actuales del perfil
    res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
    datos_perfil = res.data if res.data else {}

    # 2. Formulario de Datos Personales
    with st.container():
        st.write("### 📝 Datos Personales")
        
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre", value=datos_perfil.get("nombre", ""))
            apellidos = st.text_input("Apellidos", value=datos_perfil.get("apellidos", ""))
        
        with col2:
            telefono = st.text_input("Teléfono", value=datos_perfil.get("telefono", ""))
            direccion = st.text_input("Dirección", value=datos_perfil.get("direccion", ""))
        
        ciudad = st.text_input("Ciudad", value=datos_perfil.get("ciudad", ""))

        st.write("---")
        st.write(f"**Email de cuenta:** {st.session_state.user.email}")
        st.write(f"**Rol de usuario:** {st.session_state.user_role.upper()}")
        
        # 3. Botón Guardar
        if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
            try:
                actualizacion = {
                    "nombre": nombre,
                    "apellidos": apellidos,
                    "telefono": telefono,
                    "direccion": direccion,
                    "ciudad": ciudad
                }
                
                supabase.table("profiles").update(actualizacion).eq("id", st.session_state.user.id).execute()
                st.success("¡Perfil actualizado correctamente!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- PANTALLA: BIBLIOTECA ---
elif st.session_state.sub_pantalla == "biblioteca":
    st.markdown('<p class="titulo-pantalla" style="font-size: 30px;">BIBLIOTECA</p>', unsafe_allow_html=True)
    try:
        res_b = supabase.table("biblioteca").select("*").order("orden").execute()
        leyes = res_b.data
        if leyes:
            st.write("---")
            # Cabecera de la lista (opcional)
            h1, h2 = st.columns([4, 1])
            h1.caption("NOMBRE DEL TEMA / LEY")
            h2.caption("ACCIÓN")
            for ley in leyes:
                nombre = ley.get('name')
                url = ley.get('url_pdf')
                orden = ley.get('orden') or ley.get('id')
                if nombre and url:
                    # Contenedor de fila con columnas muy ajustadas
                    with st.container():
                        col_txt, col_btn = st.columns([4, 1])
                        with col_txt:
                            # Texto principal y secundario en la misma zona
                            st.markdown(f'<p class="texto-ley">#{orden} - {nombre}</p>', unsafe_allow_html=True)
                        with col_btn:
                            # Botón pequeño (Streamlit usa el estilo del CSS arriba)
                            st.link_button("📥 PDF", url, use_container_width=True)
                        # Separador casi invisible
                        st.markdown('<div style="margin-bottom: 5px; border-bottom: 1px solid rgba(255,255,255,0.05);"></div>', unsafe_allow_html=True)
        else:
            st.info("Biblioteca vacía.")        
    except Exception as e:
        st.error(f"Error: {e}")

# --- PANTALLA: SELECCIÓN DE TEMA (EXÁMENES) ---
elif st.session_state.sub_pantalla == "seleccion_tema":
    st.markdown('<p class="titulo-pantalla">MODO DE EXAMEN</p>', unsafe_allow_html=True)
    
    # Abrimos el contenedor con la clase CSS personalizada
    st.markdown('<div class="contenedor-test">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🇬🇧\n\nEXAMEN DE INGLÉS", use_container_width=True):
            cambiar_vista("test_ingles")
            st.rerun()

    with col2:
        if st.button("📚\n\nEXAMEN POR TEMAS", use_container_width=True):
            cambiar_vista("test_por_temas")
            st.rerun()

    with col3:
        if st.button("⏱️\n\nSIMULACRO EXAMEN", use_container_width=True):
            cambiar_vista("test_simulacro")
            st.rerun()
            
    # Cerramos el contenedor
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("---")
    # Este botón de volver NO se verá afectado por el estilo anterior
    if st.button("⬅️ Volver al Centro de Control"):
        cambiar_vista("menu_principal")
        st.rerun()
        
elif st.session_state.sub_pantalla == "test_simulacro":
    st.markdown('<p class="titulo-pantalla">SIMULACRO DE EXAMEN</p>', unsafe_allow_html=True)

    # --- LÓGICA DE CARGA INICIAL ---
    if not st.session_state.preguntas_simulacro:
        try:
            # Traemos, por ejemplo, 20 preguntas aleatorias de la tabla preguntas
            res = supabase.table("preguntas").select("*").execute()
            if res.data:
                todas = res.data
                random.shuffle(todas)
                st.session_state.preguntas_simulacro = todas[:20] # Ajusta el número aquí
                st.session_state.indice_pregunta = 0
                st.session_state.respuestas_usuario = {}
                st.session_state.examen_finalizado = False
                st.rerun()
        except Exception as e:
            st.error(f"Error al cargar preguntas: {e}")
            if st.button("Volver"): cambiar_vista("seleccion_tema"); st.rerun()

    # --- PANTALLA DE RESULTADOS FINALES ---
    if st.session_state.examen_finalizado:
        st.success("✅ Examen completado")
        # Aquí calcularemos la nota
        aciertos = 0
        preguntas = st.session_state.preguntas_simulacro
        for i, p in enumerate(preguntas):
            if st.session_state.respuestas_usuario.get(i) == p['correcta']:
                aciertos += 1
        st.metric("TU PUNTUACIÓN", f"{aciertos} / {len(preguntas)}")
        if st.button("VOLVER AL MENÚ"):
            st.session_state.preguntas_simulacro = []
            cambiar_vista("seleccion_tema")
            st.rerun()
        return

    # --- INTERFAZ DEL TEST ---
    preguntas = st.session_state.preguntas_simulacro
    idx = st.session_state.indice_pregunta
    p_actual = preguntas[idx]

    # Barra de progreso
    progreso = (idx + 1) / len(preguntas)
    st.progress(progreso, text=f"Pregunta {idx + 1} de {len(preguntas)}")

    # Enunciado
    st.markdown(f"### {p_actual['enunciado']}")
    
    # Opciones
    opciones = {
        "A": p_actual['opcion_a'],
        "B": p_actual['opcion_b'],
        "C": p_actual['opcion_c']
    }
    
    # Usamos un radio button para la selección
    # El index=None hace que no haya ninguna marcada por defecto
    seleccion = st.radio(
        "Selecciona tu respuesta:",
        options=["A", "B", "C"],
        format_func=lambda x: f"{x}) {opciones[x]}",
        key=f"preg_{idx}"
    )

    st.write("---")
    col_prev, col_next = st.columns(2)

    with col_prev:
        if idx > 0:
            if st.button("⬅️ Anterior", use_container_width=True):
                st.session_state.indice_pregunta -= 1
                st.rerun()

    with col_next:
        # Guardamos la respuesta antes de pasar
        st.session_state.respuestas_usuario[idx] = seleccion
        
        if idx < len(preguntas) - 1:
            if st.button("Siguiente ➡️", use_container_width=True):
                st.session_state.indice_pregunta += 1
                st.rerun()
        else:
            if st.button("🏁 FINALIZAR EXAMEN", type="primary", use_container_width=True):
                st.session_state.examen_finalizado = True
                st.rerun()
# --- PANTALLA: PANEL ADMIN ---
elif st.session_state.sub_pantalla == "panel_admin":
    st.markdown('<p class="titulo-pantalla">GESTIÓN PREGUNTAS</p>', unsafe_allow_html=True)
    st.write("Panel exclusivo para añadir y editar el banco de preguntas.")
