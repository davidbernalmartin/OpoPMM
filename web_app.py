import streamlit as st
from supabase import create_client
import random
import pandas as pd

def limpiar_estado_examen():
    st.session_state.preguntas_examen = []
    st.session_state.indice_pregunta = 0
    st.session_state.respuestas_usuario = {}
    st.session_state.examen_finalizado = False
    st.session_state.paso_configuracion = "botones" # IMPORTANTE: Volver al inicio
    st.session_state.modo_seleccionado = None
    st.session_state.temas_seleccionados = []

def mostrar_examen(titulo, lista_preguntas):
    st.markdown(f'<div class="titulo-pantalla">{titulo}</div>', unsafe_allow_html=True)
    # 1. MODO REVISIÓN INDIVIDUAL (Pantalla Completa)
    if st.session_state.get("ver_revision", False):
        idx_rev = st.session_state.get("indice_revision", 0)
        p = lista_preguntas[idx_rev]
        resp_usuario = st.session_state.respuestas_usuario.get(idx_rev)
        es_correcta = resp_usuario == p['correcta']

        st.progress((idx_rev + 1) / len(lista_preguntas), text=f"Revisando Pregunta {idx_rev + 1} de {len(lista_preguntas)}")

        st.markdown(f"#### {p['enunciado']}")

        # --- SECCIÓN DE OPCIONES (Alineación Corregida) ---
        opciones = [("A", p['opcion_a']), ("B", p['opcion_b']), ("C", p['opcion_c'])]
        for letra, texto in opciones:
            base_style = "padding: 12px; border-radius: 10px; margin: 8px 0; border-left: 5px solid "
            if letra == p['correcta']:
                # OPCIÓN CORRECTA: Fondo verde y borde verde
                st.markdown(f"""
                    <div style="{base_style} #2ecc71; background-color: rgba(46, 204, 113, 0.15);">
                        <b style="color: white;">{letra}) {texto}</b> <span style="color: #2ecc71; margin-left: 10px;">(Correcta)</span>
                    </div>
                """, unsafe_allow_html=True)
                
            elif letra == resp_usuario and not es_correcta:
                # OPCIÓN FALLADA: Fondo rojo y borde rojo
                st.markdown(f"""
                    <div style="{base_style} #e74c3c; background-color: rgba(231, 76, 60, 0.15);">
                        <span style="color: white;">{letra}) {texto}</span> <span style="color: #e74c3c; margin-left: 10px;">(Tu elección)</span>
                    </div>
                """, unsafe_allow_html=True)
                
            else:
                # OPCIÓN NEUTRA: Sin fondo pero con el MISMO margen y borde transparente para alinear
                st.markdown(f"""
                    <div style="{base_style} transparent; background-color: transparent;">
                        <span style="color: #bdc3c7;">{letra}) {texto}</span>
                    </div>
                """, unsafe_allow_html=True)

        # --- SECCIÓN DE EXPLICACIÓN (Corregida para evitar errores de renderizado) ---
        st.write("---")
        # 1. Recuperamos la explicación
        exp_raw = p.get('explicacion', '')
        # 2. Solo dibujamos el cuadro si realmente hay contenido
        # Comprobamos que no sea None, ni una cadena vacía, ni solo espacios
        if exp_raw and str(exp_raw).strip():
            explicacion_completa = f"""
            <div style="background-color: rgba(0, 150, 255, 0.1); 
                        padding: 20px; 
                        border-radius: 10px; 
                        border-left: 5px solid #0891B2;
                        margin-bottom: 20px;">
                <p style="margin-top:0; margin-bottom: 10px; font-weight: bold; color: #0891B2; font-size: 1.1rem;">
                    💡 EXPLICACIÓN
                </p>
                <div style="font-size: 1rem; line-height: 1.6; color: #e0e0e0;">
                    {exp_raw}
                </div>
            </div>
            """
            st.markdown(explicacion_completa, unsafe_allow_html=True)
        else:
            # Si no hay explicación, mostramos un mensaje discreto o nada
            st.caption("No hay explicación disponible para esta pregunta.")
        st.write("---")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if idx_rev > 0:
                if st.button("⬅️ ANTERIOR", key="rev_prev", use_container_width=True):
                    st.session_state.indice_revision -= 1
                    st.rerun()
        with c2:
            if st.button("VOLVER AL RESUMEN", use_container_width=True):
                st.session_state.ver_revision = False
                st.rerun()
        with c3:
            if idx_rev < len(lista_preguntas) - 1:
                if st.button("SIGUIENTE ➡️", key="rev_next", use_container_width=True):
                    st.session_state.indice_revision += 1
                    st.rerun()

    # 2. PANTALLA DE RESULTADOS (Resumen de Notas)
    elif st.session_state.examen_finalizado:
        total = len(lista_preguntas)
        aciertos = sum(1 for i, p in enumerate(lista_preguntas) if st.session_state.respuestas_usuario.get(i) == p['correcta'])
        fallos = sum(1 for i, p in enumerate(lista_preguntas) if st.session_state.respuestas_usuario.get(i) is not None and st.session_state.respuestas_usuario.get(i) != p['correcta'])
        sin_responder = total - (aciertos + fallos)

        netas = aciertos - (fallos * 0.33)
        nota_diez = (max(0, netas) / total) * 10 

        st.markdown('<h2 style="text-align: center;">📊 RESULTADOS DEL EXAMEN</h2>', unsafe_allow_html=True)
        st.write("###")

        # Fila 1: Métricas centradas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div style="text-align: center;"><p style="font-size: 1.5rem; margin-bottom:0;">🟢 Aciertos</p><h1 style="color: #2ecc71; margin-top:0;">{aciertos}</h1></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="text-align: center;"><p style="font-size: 1.5rem; margin-bottom:0;">🔴 Fallos</p><h1 style="color: #e74c3c; margin-top:0;">{fallos}</h1></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div style="text-align: center;"><p style="font-size: 1.5rem; margin-bottom:0;">⚪ En blanco</p><h1 style="color: #bdc3c7; margin-top:0;">{sin_responder}</h1></div>', unsafe_allow_html=True)

        st.write("---")

        # Fila 2: Tarjetas de Netas y Nota
        c_netas, c_nota = st.columns(2)
        with c_netas:
            st.markdown(f"""<div style="background-color: #6D28D9; padding: 25px; border-radius: 15px; text-align: center; border: 1px solid #4C1D95;">
                <p style="margin:0; font-size: 1.3rem; color: #EDE9FE; font-weight: bold;">PREGUNTAS NETAS</p>
                <h1 style="margin:0; color: white; font-size: 3.5rem;">{netas:.2f}</h1>
            </div>""", unsafe_allow_html=True)
        with c_nota:
            st.markdown(f"""<div style="background-color: #0891B2; padding: 25px; border-radius: 15px; text-align: center; border: 1px solid #164E63;">
                <p style="margin:0; font-size: 1.3rem; color: #CFFAFE; font-weight: bold;">NOTA SOBRE 10</p>
                <h1 style="margin:0; color: white; font-size: 3.5rem;">{nota_diez:.2f}</h1>
            </div>""", unsafe_allow_html=True)

        st.write("###")
        col_rev, col_fin = st.columns(2)
        with col_rev:
            if st.button("🔍 REVISAR PREGUNTA A PREGUNTA", use_container_width=True):
                st.session_state.ver_revision = True
                st.session_state.indice_revision = 0
                st.rerun()
        with col_fin:
            if st.button("🏁 FINALIZAR Y VOLVER", use_container_width=True, type="primary"):
                st.session_state.ver_revision = False
                limpiar_estado_examen()
                st.session_state.sub_pantalla = "seleccion_tema"
                st.rerun()

    # 3. INTERFAZ DEL TEST (En curso)
    else:
        idx = st.session_state.indice_pregunta
        p_actual = lista_preguntas[idx]

        st.progress((idx + 1) / len(lista_preguntas), text=f"Pregunta {idx + 1} de {len(lista_preguntas)}")
        st.markdown(f"#### {p_actual['enunciado']}")
        
        opciones_letras = ["A", "B", "C"]
        respuesta_guardada = st.session_state.respuestas_usuario.get(idx)
        indice_a_mostrar = opciones_letras.index(respuesta_guardada) if respuesta_guardada in opciones_letras else None

        opciones_texto = {"A": p_actual['opcion_a'], "B": p_actual['opcion_b'], "C": p_actual['opcion_c']}

        seleccion = st.radio(
            "Selecciona tu respuesta:",
            options=opciones_letras,
            format_func=lambda x: f"{x}) {opciones_texto[x]}",
            index=indice_a_mostrar,
            key=f"radio_preg_{idx}"
        )

        if seleccion:
            st.session_state.respuestas_usuario[idx] = seleccion

        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if idx > 0:
                if st.button("⬅️ ANTERIOR", use_container_width=True):
                    st.session_state.indice_pregunta -= 1
                    st.rerun()
        with col2:
            if idx < len(lista_preguntas) - 1:
                if st.button("SIGUIENTE ➡️", use_container_width=True):
                    st.session_state.indice_pregunta += 1
                    st.rerun()
            else:
                if st.button("🏁 CORREGIR EXAMEN", type="primary", use_container_width=True):
                    st.session_state.examen_finalizado = True
                    st.rerun()

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
if "preguntas_examen" not in st.session_state:
    st.session_state.preguntas_examen = []
if "indice_pregunta" not in st.session_state:
    st.session_state.indice_pregunta = 0
if "respuestas_usuario" not in st.session_state:
    st.session_state.respuestas_usuario = {}
if "examen_finalizado" not in st.session_state:
    st.session_state.examen_finalizado = False
if "configurando_examen" not in st.session_state:
    st.session_state.configurando_examen = False
if "modo_seleccionado" not in st.session_state:
    st.session_state.modo_seleccionado = None
if "paso_configuracion" not in st.session_state:
    st.session_state.paso_configuracion = "botones"

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
            limpiar_estado_examen()
            cambiar_vista("seleccion_tema")
            st.rerun()

        # 5. Gestión Preguntas (Solo ADMIN)
        if st.session_state.user_role == "admin":
            st.write("")
            st.markdown('<p style="font-size: 11px; opacity: 0.6; margin-left: 5px; letter-spacing: 1px;">ADMINISTRACIÓN</p>', unsafe_allow_html=True)
            if st.button("⚙️ GESTIÓN PREGUNTAS", use_container_width=True):
                cambiar_vista("admin_preguntas")
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
    st.markdown(f'<div class="titulo-pantalla">OpoPMM</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("---")
        if st.button("¡VAMOS A POR LA PLAZA!", use_container_width=True, type="primary"):
            cambiar_vista("login")
            st.rerun()

# --- PANTALLA: LOGIN / REGISTRO ---
elif st.session_state.sub_pantalla == "login":
    st.markdown(f'<div class="titulo-pantalla">ACCESO</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Entrar", "Registrarse"])
    
    with tabs[0]:
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Contraseña", type="password", key="login_pw")
        if st.button("INICIAR SESIÓN", use_container_width=True, type="primary"):
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
                    cambiar_vista("menu_principal")
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
        if st.button("CREAR CUENTA", use_container_width=True):
            try:
                # Si tienes la confirmación desactivada en Supabase, entra directo
                res = supabase.auth.sign_up({"email": n_email, "password": n_pw})
                st.success("¡Cuenta creada! Intenta loguearte ahora.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- PANTALLA: MENÚ PRINCIPAL (RESUMEN) ---
elif st.session_state.sub_pantalla == "menu_principal":
    st.markdown(f'<div class="titulo-pantalla">CENTRO DE CONTROL</div>', unsafe_allow_html=True)
    st.info("Bienvenido. Utiliza el menú de la izquierda para navegar por la aplicación.")
    
    # Dashboard rápido
    c1, c2, c3 = st.columns(3)
    c1.metric("Nota Media", "7.2", "0.5")
    c2.metric("Test Completados", "24")
    c3.metric("Días para Examen", "124")

# --- PANTALLA: ESTADÍSTICAS ---
elif st.session_state.sub_pantalla == "stats":
    st.markdown(f'<div class="titulo-pantalla">PROGRESO</div>', unsafe_allow_html=True)
    st.write("Aquí verás tus gráficos de evolución por temas.")

# --- PANTALLA: PERFIL ---
elif st.session_state.sub_pantalla == "perfil":
    st.markdown(f'<div class="titulo-pantalla">MI PERFIL</div>', unsafe_allow_html=True)
    
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
    st.markdown(f'<div class="titulo-pantalla">BIBLIOTECA</div>', unsafe_allow_html=True)
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
    
    # --- PASO 1: LOS 3 BOTONES PRINCIPALES ---
    if st.session_state.paso_configuracion == "botones":
        st.markdown(f'<div class="titulo-pantalla">MODO EXAMEN</div>', unsafe_allow_html=True)
        st.markdown('<div class="contenedor-test">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🇬🇧\n\nEXAMEN DE INGLÉS", use_container_width=True):
                st.session_state.modo_seleccionado = "ingles"
                st.session_state.paso_configuracion = "seleccion_cantidad"
                st.rerun()
        with col2:
            if st.button("📚\n\nEXAMEN POR TEMAS", use_container_width=True):
                st.session_state.modo_seleccionado = "por_temas"
                st.session_state.paso_configuracion = "seleccion_temas" # Va a la lista de temas
                st.rerun()
        with col3:
            if st.button("⏱️\n\nSIMULACRO EXAMEN", use_container_width=True):
                st.session_state.modo_seleccionado = "simulacro"
                st.session_state.paso_configuracion = "seleccion_cantidad"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- PASO 2: SELECCIÓN DE TEMAS (Solo para "Por Temas") ---
    elif st.session_state.paso_configuracion == "seleccion_temas":
        st.markdown(f'<div class="titulo-pantalla">SELECCION DE TEMAS</div>', unsafe_allow_html=True)
        try:
            # Consultamos la tabla temas para listar los temas
            res = supabase.table("temas").select("id, nombre").order("id").neq("id",1).execute()
            temas_db = res.data
            
            # Filtramos el ID 1 (Inglés) para que no salga en "Por Temas"
            opciones = {f"Tema {t['nombre']}": t['id'] for t in temas_db if t['id'] != 1}
            
            seleccion = st.multiselect("Selecciona una o varias leyes:", options=list(opciones.keys()))
            
            st.write("---")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("⬅️ VOLVER", use_container_width=True):
                    st.session_state.paso_configuracion = "botones"
                    st.rerun()
            with c2:
                if st.button("CONTINUAR ➡️", type="primary", use_container_width=True, disabled=not seleccion):
                    # Guardamos los IDs de los temas elegidos
                    st.session_state.temas_seleccionados = [opciones[s] for s in seleccion]
                    st.session_state.paso_configuracion = "seleccion_cantidad"
                    st.rerun()
        except Exception as e:
            st.error(f"Error cargando temas: {e}")

    # --- PASO 3: SELECCIÓN DE CANTIDAD (Para todos) ---
    elif st.session_state.paso_configuracion == "seleccion_cantidad":
        st.markdown(f'<div class="titulo-pantalla">NUMERO DE PREGUNTAS</div>', unsafe_allow_html=True)
        st.write(f"Modo: **{st.session_state.modo_seleccionado.upper()}**")
        
        cantidad = st.select_slider(
            "¿Cuántas preguntas quieres responder?",
            options=[10, 20, 40, 80, 100],
            value=20
        )
        
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅️ VOLVER", use_container_width=True):
                # Si venía de temas, vuelve a temas. Si no, a los botones.
                if st.session_state.modo_seleccionado == "por_temas":
                    st.session_state.paso_configuracion = "seleccion_temas"
                else:
                    st.session_state.paso_configuracion = "botones"
                st.rerun()
        with c2:
            if st.button("🚀 EMPEZAR EXAMEN", type="primary", use_container_width=True):
                st.session_state.cantidad_preguntas = cantidad
                st.session_state.sub_pantalla = f"test_{st.session_state.modo_seleccionado}"
                st.rerun()

# --- MODO 1: INGLÉS ---
elif st.session_state.sub_pantalla == "test_ingles":
    if not st.session_state.preguntas_examen:
        limite_elegido = st.session_state.get("cantidad_preguntas", 20)
        try:
            # Traemos TODAS las de inglés
            res = supabase.table("preguntas").select("*").eq("tema_id", 1).execute()
            
            if res.data:
                todo_el_banco = res.data
                random.shuffle(todo_el_banco) # Barajamos todo el mazo primero
                st.session_state.preguntas_examen = todo_el_banco[:limite_elegido] # Cortamos
                
                st.session_state.indice_pregunta = 0
                st.session_state.respuestas_usuario = {}
                st.session_state.examen_finalizado = False
                st.rerun()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            if st.button("Volver al menú"):
                limpiar_estado_examen()
                st.rerun()
    
    # IMPORTANTE: Esto queda fuera del bloque 'if not st.session_state.preguntas_examen'
    if st.session_state.preguntas_examen:
        mostrar_examen("EXAMEN DE INGLÉS", st.session_state.preguntas_examen)

# --- MODO 2: POR TEMAS ---
elif st.session_state.sub_pantalla == "test_por_temas":
    if not st.session_state.preguntas_examen:
        ids_seleccionados = st.session_state.get("temas_seleccionados", [])
        limite_elegido = st.session_state.get("cantidad_preguntas", 20)
        try:
            # Traemos todo lo que NO sea inglés (ID != 1)
            res = supabase.table("preguntas").select("*").in_("tema_id", ids_seleccionados).execute()
            if res.data:
                todo_el_banco = res.data
                random.shuffle(todo_el_banco)
                st.session_state.preguntas_examen = todo_el_banco[:limite_elegido]
                
                st.session_state.indice_pregunta = 0
                st.session_state.respuestas_usuario = {}
                st.session_state.examen_finalizado = False
                st.rerun()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            if st.button("Volver al menú"):
                limpiar_estado_examen()
                st.rerun()
    
    # IMPORTANTE: Esto queda fuera del bloque 'if not st.session_state.preguntas_examen'
    if st.session_state.preguntas_examen:
        mostrar_examen("EXAMEN POR TEMAS", st.session_state.preguntas_examen)

# --- MODO 3: SIMULACRO ---
elif st.session_state.sub_pantalla == "test_simulacro":
    if not st.session_state.preguntas_examen:
        limite_elegido = st.session_state.get("cantidad_preguntas", 20)
        try:
            # Traemos todo lo que NO sea inglés (ID != 1)
            res = supabase.table("preguntas").select("*").neq("tema_id", 1).execute()
            
            if res.data:
                todo_el_banco = res.data
                random.shuffle(todo_el_banco)
                st.session_state.preguntas_examen = todo_el_banco[:limite_elegido]
                
                st.session_state.indice_pregunta = 0
                st.session_state.respuestas_usuario = {}
                st.session_state.examen_finalizado = False
                st.rerun()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            if st.button("Volver al menú"):
                limpiar_estado_examen()
                st.rerun()
    
    # IMPORTANTE: Esto queda fuera del bloque 'if not st.session_state.preguntas_examen'
    if st.session_state.preguntas_examen:
        mostrar_examen("SIMULACRO GENERAL", st.session_state.preguntas_examen)
                        
elif st.session_state.sub_pantalla == "admin_preguntas":
    st.markdown('<div class="titulo-pantalla">PANEL DE GESTIÓN</div>', unsafe_allow_html=True)

    # 1. CARGAMOS TEMAS (Diccionario para mapear ID -> Nombre y viceversa)
    res_temas = supabase.table("temas").select("id, nombre").execute()
    temas_db = res_temas.data
    id_a_nombre = {t['id']: t['nombre'] for t in temas_db}
    nombre_a_id = {t['nombre']: t['id'] for t in temas_db}

    # 2. CARGAMOS PREGUNTAS
    res_p = supabase.table("preguntas").select("*").order("id", desc=True).execute()
    
    if res_p.data:
        # Convertimos a DataFrame para manipularlo fácil
        df = pd.DataFrame(res_p.data)
        
        # CREAMOS LA COLUMNA MÁGICA: Mapeamos el tema_id al nombre real
        df['tema_nombre'] = df['tema_id'].map(id_a_nombre)
        
        # --- TABLA INTERACTIVA ---
        st.write("### 📋 Banco de Preguntas")
        
        # Configuramos la visualización
        event = st.dataframe(
            df,
            column_order=("id", "enunciado", "tema_nombre"), # Usamos la nueva columna
            column_config={
                "id": st.column_config.NumberColumn("ID", width=40),
                "enunciado": st.column_config.TextColumn("Enunciado", width="600"),
                "tema_nombre": st.column_config.TextColumn("Tema", width="medium"),
            },
            hide_index=True,
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        # 3. LÓGICA DE SELECCIÓN
        seleccion = event.selection.rows
        if seleccion:
            # Extraemos la fila seleccionada del dataframe original
            st.session_state.p_seleccionada = df.iloc[seleccion[0]].to_dict()
    
    # --- FORMULARIO DE EDICIÓN (Igual que antes pero usando st.session_state.p_seleccionada) ---
    p = st.session_state.get("p_seleccionada", None)
    
    st.divider()
    if p:
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.caption("ENUNCIADO DE LA PREGUNTA:")
                f_enun = st.text_area("##enun", value=p['enunciado'], height=150, label_visibility="collapsed")
            with col2:
                st.caption("EXPLICACIÓN / BASE LEGAL:")
                f_exp = st.text_area("##exp", value=p.get('explicacion', ''), height=150, label_visibility="collapsed")

            col3, col4 = st.columns(2)
            with col3:
                st.caption("OPCIONES DE RESPUESTA:")
                f_a = st.text_input("A", value=p['opcion_a'])
                f_b = st.text_input("B", value=p['opcion_b'])
                f_c = st.text_input("C", value=p['opcion_c'])
            with col4:
                st.caption("CONFIGURACIÓN:")
                f_corr = st.selectbox("Correcta", ["A", "B", "C"], 
                                     index=["A", "B", "C"].index(p['correcta']))
                
                # Selector de tema (usando nombres para que sea humano)
                nombres_temas = sorted(list(nombre_a_id.keys()))
                idx_tema = nombres_temas.index(p['tema_nombre']) if p['tema_nombre'] in nombres_temas else 0
                f_tema_sel = st.selectbox("Tema", nombres_temas, index=idx_tema)

    # --- BOTONERA ---
    st.write("###")
    b1, b2, b3, b4, b5 = st.columns(5)
    
    with b1:
        if st.button("➕ NUEVA", use_container_width=True):
            st.session_state.p_seleccionada = None
            st.rerun()
    
    with b4:
        if st.button("💾 GUARDAR", type="primary", use_container_width=True):
            if p:
                upd = {
                    "enunciado": f_enun, "explicacion": f_exp, "opcion_a": f_a,
                    "opcion_b": f_b, "opcion_c": f_c, "correcta": f_corr,
                    "tema_id": nombres_a_id[f_tema]
                }
                supabase.table("preguntas").update(upd).eq("id", p['id']).execute()
                st.success("¡Actualizado!")
                st.rerun()

    with b5:
        if st.button("🗑️ ELIMINAR", use_container_width=True):
            if p:
                supabase.table("preguntas").delete().eq("id", p['id']).execute()
                st.session_state.p_seleccionada = None
                st.rerun()
