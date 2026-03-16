import streamlit as st
from supabase import create_client
import random

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="OpoTests PMM - Web", page_icon="👮‍♂️", layout="wide")

# --- 2. CONEXIÓN A SUPABASE ---
# Asegúrate de tener estas keys en tu archivo .streamlit/secrets.toml
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- 3. ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    /* Fondo y colores base */
    .stApp { background-color: #2c3e50; color: white; }

    /* Estilo uniforme para todos los botones */
    div.stButton > button {
        min-height: 70px !important;
        font-size: 18px !important;
        border-radius: 12px !important;
        white-space: normal !important;
        transition: 0.3s;
    }

    /* Cabeceras de sección azul oscuro */
    .seccion-titulo {
        background-color: #34495e; 
        padding: 15px; 
        border-radius: 15px; 
        text-align: center; 
    }

    /* Estilo para las métricas de resultados */
    [data-testid="stMetricValue"] { font-size: 30px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. LÓGICA DE ESTADO (SESSION STATE) ---
if "examen_iniciado" not in st.session_state:
    st.session_state.examen_iniciado = False  # False, True, o "FINALIZADO"
    st.session_state.pantalla = "menu"        # "menu", "biblioteca", "examen"
    st.session_state.sub_pantalla = "inicio"  # "inicio", "teoria_opciones", "seleccion_tema", "config"
    st.session_state.preguntas = []
    st.session_state.indice = 0
    st.session_state.aciertos = 0
    st.session_state.fallos = 0
    st.session_state.respuesta_dada = None
    st.session_state.tema_elegido_id = None
    st.session_state.tema_elegido_nombre = ""
    st.session_state.num_preguntas = 20

# --- 5. FUNCIONES DE DATOS ---
def iniciar_examen(temas_ids, cantidad):
    try:
        # Consulta a Supabase filtrando por los temas seleccionados
        res = supabase.table("preguntas").select("*").in_("tema_id", temas_ids).execute()
        if res.data:
            lista = res.data
            random.shuffle(lista)
            st.session_state.preguntas = lista[:cantidad]
            st.session_state.examen_iniciado = True
            st.session_state.indice = 0
            st.session_state.aciertos = 0
            st.session_state.fallos = 0
            st.session_state.respuesta_dada = None
        else:
            st.warning("No se encontraron preguntas para esta selección.")
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")

def obtener_biblioteca_leyes():
    try:
        return supabase.table("biblioteca").select("*").order("orden").execute().data
    except:
        return []

# --- 6. INTERFAZ DE USUARIO ---

# SI EL EXAMEN NO HA EMPEZADO, MOSTRAR MENÚS
if st.session_state.examen_iniciado is False:
    # --- CABECERA COMÚN OPTIMIZADA ---
    # Inyectamos CSS específico para centrar verticalmente los elementos de las columnas
    st.markdown("""
        <style>
        /* Fuerza la alineación vertical central en todas las columnas de la cabecera */
        [data-testid="stHorizontalBlock"] {
            align-items: center !important;
        }
        /* Ajuste fino para que el contenedor del título no tenga márgenes extra */
        .seccion-titulo h3 {
            line-height: 1.2;
        }
        </style>
    """, unsafe_allow_html=True)

    # Definimos las columnas (Botón izquierda, Título centro, Botón derecha)
    col_izq, col_titulo, col_der = st.columns([0.2, 0.8, 0.2])

    with col_izq:
        # Botón invisible o de utilidad a la izquierda para equilibrar
        if st.button("❓", use_container_width=True, key="btn_ayuda_top"):
            st.toast("OPOTESTS PMM - Sistema de preparación", icon="👮‍♂️")

    with col_titulo:
        # El título central
        st.markdown('<div class="seccion-titulo"><h3 style="margin:0; color: white;">OPOTESTS PMM</h3></div>', unsafe_allow_html=True)

    with col_der:
        # El botón de perfil a la derecha
        if st.button("👤 Perfil", use_container_width=True, key="btn_perfil_top"):
            st.toast("Módulo de usuario próximamente...", icon="🔑")

    st.divider()

    # --- PANTALLA: MENÚ PRINCIPAL ---
    if st.session_state.pantalla == "menu":
        
        # Botón para retroceder en los niveles del menú
        if st.session_state.sub_pantalla != "inicio":
            if st.button("⬅ Volver"):
                if st.session_state.sub_pantalla in ["teoria_opciones", "config_ingles", "config_simulacro"]:
                    st.session_state.sub_pantalla = "inicio"
                elif st.session_state.sub_pantalla in ["seleccion_tema", "config_examen_tema"]:
                    st.session_state.sub_pantalla = "teoria_opciones"
                st.rerun()

        # NIVEL 1: HOME
        if st.session_state.sub_pantalla == "inicio":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📚 TEORÍA", use_container_width=True):
                    st.session_state.sub_pantalla = "teoria_opciones"
                    st.rerun()
            with col2:
                if st.button("🇬🇧 INGLÉS", use_container_width=True):
                    st.session_state.tema_elegido_nombre = "Examen de Inglés"
                    st.session_state.sub_pantalla = "config_ingles"
                    st.rerun()
            
            st.divider()
            col3, col4 = st.columns(2)
            with col3:
                if st.button("📖 BIBLIOTECA", use_container_width=True):
                    st.session_state.pantalla = "biblioteca"
                    st.rerun()
            with col4:
                if st.button("📊 ESTADÍSTICAS", use_container_width=True):
                    st.toast("Sección en construcción")

        # NIVEL 2: OPCIONES DE TEORÍA
        elif st.session_state.sub_pantalla == "teoria_opciones":
            st.subheader("¿Qué tipo de test de teoría quieres hacer?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📂 POR TEMAS", use_container_width=True):
                    st.session_state.sub_pantalla = "seleccion_tema"
                    st.rerun()
            with c2:
                if st.button("⏱️ SIMULACRO GENERAL", use_container_width=True):
                    st.session_state.tema_elegido_nombre = "Simulacro de Examen"
                    st.session_state.sub_pantalla = "config_simulacro"
                    st.rerun()

        # NIVEL 3: SELECCIÓN DE TEMA ESPECÍFICO
        elif st.session_state.sub_pantalla == "seleccion_tema":
            st.subheader("Elige un tema para examinarte")
            try:
                res_temas = supabase.table("temas").select("id, nombre").neq("id", 1).order("id").execute().data
                cols = st.columns(2)
                for i, t in enumerate(res_temas):
                    with cols[i % 2]:
                        if st.button(t['nombre'], key=f"t_{t['id']}", use_container_width=True):
                            st.session_state.tema_elegido_id = t['id']
                            st.session_state.tema_elegido_nombre = t['nombre']
                            st.session_state.sub_pantalla = "config_examen_tema"
                            st.rerun()
            except:
                st.error("No se pudieron cargar los temas.")

        # NIVEL FINAL: CONFIGURAR CANTIDAD DE PREGUNTAS
        elif st.session_state.sub_pantalla in ["config_ingles", "config_simulacro", "config_examen_tema"]:
            st.markdown(f"### Configuración: {st.session_state.tema_elegido_nombre}")
            
            with st.container(border=True):
                num = st.select_slider("Selecciona el número de preguntas:", options=[5, 10, 20, 50, 100], value=20)
                
                if st.button("🚀 COMENZAR EXAMEN", type="primary", use_container_width=True):
                    # Determinar qué IDs cargar
                    if st.session_state.sub_pantalla == "config_ingles":
                        ids = [1] # Inglés suele ser ID 1
                    elif st.session_state.sub_pantalla == "config_simulacro":
                        res_all = supabase.table("temas").select("id").neq("id", 1).execute().data
                        ids = [r['id'] for r in res_all]
                    else:
                        ids = [st.session_state.tema_elegido_id]
                    
                    iniciar_examen(ids, num)
                    st.rerun()

    # --- PANTALLA: BIBLIOTECA ---
    elif st.session_state.pantalla == "biblioteca":
        if st.button("⬅ Volver al Menú Principal"):
            st.session_state.pantalla = "menu"
            st.rerun()
        
        st.markdown('<div class="seccion-titulo"><h3 style="margin:0; color: white;">📂 BIBLIOTECA DE LEYES</h3></div>', unsafe_allow_html=True)
        leyes = obtener_biblioteca_leyes()
        if leyes:
            for ley in leyes:
                with st.container(border=True):
                    c_txt, c_btn = st.columns([0.7, 0.3])
                    c_txt.markdown(f"**{ley['name']}**")
                    c_btn.link_button("📄 Ver PDF", ley['url_pdf'], use_container_width=True)
        else:
            st.info("No hay documentos en la biblioteca actualmente.")

# --- SI EL EXAMEN ESTÁ EN CURSO ---
elif st.session_state.examen_iniciado is True:
    idx = st.session_state.indice
    p = st.session_state.preguntas[idx]
    total = len(st.session_state.preguntas)

    # Stats fijas arriba
    st.markdown(f"""
        <div style="background-color: #34495e; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
            <b>Pregunta {idx+1}/{total}</b> | ✅ {st.session_state.aciertos} | ❌ {st.session_state.fallos}
        </div>
    """, unsafe_allow_html=True)

    # Enunciado
    st.markdown(f"<div style='text-align: center; margin-bottom: 35px;'><b style='font-size: 24px;'>{p['enunciado']}</b></div>", unsafe_allow_html=True)

    # Respuestas
    _, col_central, _ = st.columns([0.1, 0.8, 0.1])
    with col_central:
        for letra in ["A", "B", "C"]:
            op_text = p[f'opcion_{letra.lower()}']
            icon = ""
            if st.session_state.respuesta_dada:
                if letra == p['correcta']: icon = " ✅ "
                elif letra == st.session_state.respuesta_dada: icon = " ❌ "
            
            if st.button(f"{icon}{letra}) {op_text}", key=f"pre_{idx}_{letra}", use_container_width=True, disabled=st.session_state.respuesta_dada is not None):
                st.session_state.respuesta_dada = letra
                if letra == p['correcta']: st.session_state.aciertos += 1
                else: st.session_state.fallos += 1
                st.rerun()

    # Feedback y Siguiente
    if st.session_state.respuesta_dada:
        st.info(f"💡 EXPLICACIÓN: {p['explicacion'] if p.get('explicacion') else 'Sin explicación detallada.'}")
        if st.button("Siguiente Pregunta ➔", type="primary", use_container_width=True):
            if st.session_state.indice < total - 1:
                st.session_state.indice += 1
                st.session_state.respuesta_dada = None
            else:
                st.session_state.examen_iniciado = "FINALIZADO"
            st.rerun()

# --- SI EL EXAMEN HA TERMINADO ---
elif st.session_state.examen_iniciado == "FINALIZADO":
    st.balloons()
    st.markdown('<div class="seccion-titulo"><h2 style="margin:0; color: white;">📊 RESULTADOS FINALES</h2></div>', unsafe_allow_html=True)
    
    total = len(st.session_state.preguntas)
    aciertos = st.session_state.aciertos
    fallos = st.session_state.fallos
    netas = max(0, aciertos - (fallos * 0.33))
    nota = (netas / total * 10) if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ ACIERTOS", aciertos)
    c2.metric("❌ FALLOS", fallos)
    c3.metric("⚖️ NETAS", f"{netas:.2f}")
    c4.metric("📝 NOTA", f"{nota:.2f}/10")

    st.write("")
    if st.button("🔄 Volver al Inicio", use_container_width=True, type="primary"):
        st.session_state.examen_iniciado = False
        st.session_state.pantalla = "menu"
        st.session_state.sub_pantalla = "inicio"
        st.rerun()
