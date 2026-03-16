import streamlit as st
from supabase import create_client
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="OpoTests PMM - Web", page_icon="👮‍♂️", layout="wide")

# --- CONEXIÓN A SUPABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- ESTILOS ---
st.markdown("""
    <style>
    /* Fondo de la app */
    .stApp { background-color: #2c3e50; color: white; }

    /* Los botones: solo altura mínima y que el texto no se corte */
    div.stButton > button {
        min-height: 85px !important;
        font-size: 18px !important;
        border-radius: 10px !important;
        white-space: normal !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE ESTADO ---
if "examen_iniciado" not in st.session_state:
    st.session_state.examen_iniciado = False
    st.session_state.pantalla = "menu"
    st.session_state.cantidad_preguntas = 20
    st.session_state.preguntas = []
    st.session_state.indice = 0
    st.session_state.aciertos = 0
    st.session_state.fallos = 0
    st.session_state.respuesta_dada = None

# --- FUNCIONES ---
def iniciar_examen(temas_ids, cantidad):
    try:
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
    except Exception as e:
        st.error(f"Error al cargar preguntas: {e}")

def obtener_biblioteca_leyes():
    try:
        # Traemos las leyes ordenadas por la columna 'orden'
        res = supabase.table("biblioteca").select("*").order("orden").execute()
        return res.data
    except Exception as e:
        st.error(f"Error al cargar la biblioteca: {e}")
        return []

if not st.session_state.examen_iniciado:
# --- PANTALLA 1: MENÚ PRINCIPAL (Estructura de Navegación) ---
    if st.session_state.pantalla == "menu":
                # 1. Cabecera Homogénea (la que definimos antes)
        st.markdown("""
            <style>
            [data-testid="stHorizontalBlock"] { align-items: center !important; }
            .stButton>button { border-radius: 10px; height: 60px; font-weight: bold; }
            </style>
        """, unsafe_allow_html=True)
    
        col_perfil, col_titulo = st.columns([0.2, 0.8])
        with col_perfil:
            if st.button("👤 Mi Perfil", use_container_width=True):
                st.toast("Acceso a estadísticas próximamente...", icon="🔑")
        with col_titulo:
            st.markdown("""
                <div style="background-color: #34495e; padding: 15px; border-radius: 15px; text-align: center; border-bottom: 5px solid #3498db;">
                    <h3 style='margin:0; color: white;'>OPOTESTS PMM</h3>
                </div>
            """, unsafe_allow_html=True)
    
        st.write("") # Espaciado
        
        # Inicializamos la sub-pantalla si no existe
        if "sub_pantalla" not in st.session_state:
            st.session_state.sub_pantalla = "inicio"
    
        # --- BOTÓN VOLVER (Solo aparece si no estamos en el inicio del menú) ---
        if st.session_state.sub_pantalla != "inicio":
            if st.button("⬅ Volver al Menú Principal"):
                st.session_state.sub_pantalla = "inicio"
                st.rerun()
    
        # --- SUB-PANTALLA: INICIO (DASHBOARD) ---
        if st.session_state.sub_pantalla == "inicio":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📚 TEORÍA", use_container_width=True):
                    st.session_state.sub_pantalla = "teoria_opciones"
                    st.rerun()
            with col2:
                if st.button("🇬🇧 INGLÉS", use_container_width=True):
                    # Para inglés, como es directo, podemos ir al pop-over aquí mismo
                    st.session_state.sub_pantalla = "config_ingles"
                    st.rerun()
            
            st.write("---")
            col3, col4 = st.columns(2)
            with col3:
                if st.button("📖 BIBLIOTECA", use_container_width=True):
                    st.session_state.pantalla = "biblioteca"
                    st.rerun()
            with col4:
                if st.button("👤 MI PERFIL", use_container_width=True):
                    st.toast("Próximamente...")
    
        # --- SUB-PANTALLA: OPCIONES DE TEORÍA ---
        elif st.session_state.sub_pantalla == "teoria_opciones":
            st.markdown("### 📚 Opciones de Teoría")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📂 POR TEMAS", use_container_width=True):
                    st.session_state.sub_pantalla = "seleccion_tema"
                    st.rerun()
            with col_b:
                if st.button("⏱️ SIMULACRO", use_container_width=True):
                    st.session_state.sub_pantalla = "config_simulacro"
                    st.rerun()
    
        # --- SUB-PANTALLA: SELECCIÓN DE TEMA ---
        elif st.session_state.sub_pantalla == "seleccion_tema":
            st.markdown("### 📂 Selecciona el Tema")
            # Aquí traes tus temas de la BBDD
            temas = ["Tema 1: La Constitución", "Tema 2: El Municipio", "Tema 3: Función Pública"]
            
            for tema in temas:
                if st.button(tema, use_container_width=True):
                    st.session_state.tema_elegido = tema
                    st.session_state.sub_pantalla = "config_examen_tema"
                    st.rerun()
    
        # --- SUB-PANTALLAS DE CONFIGURACIÓN FINAL (Pop-up de preguntas) ---
        elif st.session_state.sub_pantalla in ["config_simulacro", "config_examen_tema", "config_ingles"]:
            st.markdown(f"### ⚙️ Configuración del Test")
            
            if st.session_state.sub_pantalla == "config_examen_tema":
                st.info(f"Tema seleccionado: **{st.session_state.tema_elegido}**")
    
            num = st.select_slider("¿Cuántas preguntas quieres realizar?", options=[5, 10, 20, 50, 100])
            
            if st.button("🚀 COMENZAR EXAMEN", type="primary", use_container_width=True):
                st.session_state.num_preguntas = num
                st.session_state.pantalla = "examen"
                # Importante: resetear la sub-pantalla para cuando termine el examen
                st.session_state.sub_pantalla = "inicio"
                st.rerun()

    # --- MODO 2: PANEL DE BOTONES DE TEMAS ---
    elif st.session_state.pantalla == "seleccion_temas":
        # Inyectamos CSS para quitar el margen superior del contenedor del botón
        st.markdown("""
            <style>
            [data-testid="stHorizontalBlock"] {
                align-items: center !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Usamos una columna muy estrecha para el botón y el resto para el título
        col_volver, col_titulo = st.columns([0.2, 0.8])
        
        with col_volver:
            st.write(" ") # Espacio para empujar el botón hacia abajo y centrarlo con el título
            if st.button("⬅️ Volver", use_container_width=True):
                st.session_state.pantalla = "menu"
                st.rerun()

        with col_titulo:
            st.markdown("""
                <div style="background-color: #34495e; padding: 15px; border-radius: 15px; text-align: center;">
                    <h3 style='margin:0; color: white;'>📚 TEST POR TEMAS</h3>
                </div>
            """, unsafe_allow_html=True)
        
        st.write("") # Separación antes de los temas

        res_temas = supabase.table("temas").select("id, nombre").neq("id", 1).order("id").execute().data
        
        cols_temas = st.columns(2)
        for i, t in enumerate(res_temas):
            with cols_temas[i % 2]:
                if st.button(f"{t['nombre']}", key=f"btn_t_{t['id']}", use_container_width=True):
                    iniciar_examen([t['id']], st.session_state.cantidad_preguntas)
                    st.rerun()
                    
    # --- MODO 3: BIBLIOTECA DE LEYES ---
    elif st.session_state.pantalla == "biblioteca":
        # Inyectamos CSS para quitar el margen superior del contenedor del botón
        st.markdown("""
            <style>
            [data-testid="stHorizontalBlock"] {
                align-items: center !important;
            }
            </style>
        """, unsafe_allow_html=True)
        col_volver, col_titulo = st.columns([0.2, 0.8])
        
        with col_volver:
            st.write(" ") # Alineación vertical manual
            if st.button("⬅️ Volver", use_container_width=True):
                st.session_state.pantalla = "menu"
                st.rerun()

        with col_titulo:
            st.markdown("""
                <div style="background-color: #34495e; padding: 15px; border-radius: 15px; text-align: center;">
                    <h3 style='margin:0; color: white;'>📂 BIBLIOTECA DE LEYES</h3>
                </div>
            """, unsafe_allow_html=True)

        leyes = obtener_biblioteca_leyes()
        
        if not leyes:
            st.warning("Aún no hay leyes registradas en la biblioteca.")
        else:
            for ley in leyes:
                # Usamos un contenedor para que cada ley parezca una tarjeta
                with st.container(border=True):
                    col_txt, col_btn = st.columns([0.7, 0.3])
                    with col_txt:
                        st.markdown(f"**{ley['name']}**")
                    with col_btn:
                        # Botón que abre el PDF en pestaña nueva
                        st.link_button("📄 Ver PDF", ley['url_pdf'], use_container_width=True)

# --- PANTALLA 2: EL EXAMEN ---
elif st.session_state.examen_iniciado is True:
    idx = st.session_state.indice
    p = st.session_state.preguntas[idx]
    total = len(st.session_state.preguntas)

    # Panel de Stats (igual que antes)
    st.markdown(f"""
        <div style="background-color: #34495e; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
            <b>Pregunta {idx+1}/{total}</b> | ✅ {st.session_state.aciertos} | ❌ {st.session_state.fallos}
        </div>
    """, unsafe_allow_html=True)

    # Enunciado centrado y con fuente ajustada
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 35px; padding: 0 20px;'>
            <b style='font-size: 24px !important; font-weight: 500; line-height: 1.4; color: #ecf0f1;'>
                {p['enunciado']}
            </b>
        </div>
    """, unsafe_allow_html=True)

    # Bloque de respuestas (sin columnas, todo en una)
    _, col_central, _ = st.columns([0.1, 0.8, 0.1]) # Un poco más de margen para que los botones sean el centro de atención
    
    with col_central:
        for letra in ["A", "B", "C"]:
            texto_base = f"{letra}) {p[f'opcion_{letra.lower()}']}"
            
            # Lógica de Emojis INTEGRADOS en el texto
            icon_prefix = "" # Espacio vacío por defecto
            if st.session_state.respuesta_dada:
                if letra == p['correcta']:
                    icon_prefix = " ✅ " # Emoji integrado a la izquierda
                elif letra == st.session_state.respuesta_dada and letra != p['correcta']:
                    icon_prefix = " ❌ " # Emoji integrado a la izquierda
                
            texto_opcion = f"{icon_prefix} {texto_base}"
            
            # Dibujamos el botón (con el emoji integrado en el texto)
            if st.button(texto_opcion, key=f"btn_{letra}_{idx}", use_container_width=True, disabled=st.session_state.respuesta_dada is not None):
                st.session_state.respuesta_dada = letra
                if letra == p['correcta']:
                    st.session_state.aciertos += 1
                else:
                    st.session_state.fallos += 1
                st.rerun()

    # La explicación debajo de todo el bloque
    if st.session_state.respuesta_dada:
        st.markdown(f"""
            <div style="background-color: #1a252f; padding: 20px; border-radius: 10px; border-left: 5px solid #3498db; margin: 25px 0;">
                <small style="color: #3498db;"><b>💡 EXPLICACIÓN</b></small><br>
                <div style="margin-top: 10px;">{p['explicacion'] if p.get('explicacion') else 'Sin explicación.'}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Botón de Siguiente, centrado y debajo de la explicación
        _, col_btn, _ = st.columns([0.2, 0.6, 0.2])
        with col_btn:
            if st.button("Siguiente Pregunta ➔", key="btn_sig", type="primary", use_container_width=True):
                if st.session_state.indice < total - 1:
                    st.session_state.indice += 1
                    st.session_state.respuesta_dada = None
                    st.rerun()
                else:
                    st.session_state.examen_iniciado = "FINALIZADO"
                    st.rerun()

# --- PANTALLA 3: RESUMEN FINAL ---
elif st.session_state.examen_iniciado == "FINALIZADO":
    st.balloons()
    
    st.markdown("""
        <div style="background-color: #34495e; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 30px; border-bottom: 5px solid #3498db;">
            <h2 style='margin:0; color: white;'>📊 RESULTADOS DEL TEST</h2>
        </div>
    """, unsafe_allow_html=True)

    total = len(st.session_state.preguntas)
    aciertos = st.session_state.aciertos
    fallos = st.session_state.fallos
    
    # --- CÁLCULOS ---
    # Preguntas Netas: Aciertos - (Fallos * 0.33)
    netas = max(0, aciertos - (fallos * 0.33))
    # Nota sobre 10
    nota = (netas / total * 10) if total > 0 else 0
    
    # --- VISUALIZACIÓN EN 4 COLUMNAS ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("✅ ACIERTOS", aciertos)
    with col2:
        st.metric("❌ FALLOS", fallos)
    with col3:
        # Este es el dato que faltaba en la fila principal
        st.metric("⚖️ NETAS", f"{netas:.2f}")
    with col4:
        st.metric("📝 NOTA", f"{nota:.2f}/10")

    st.divider()

    # Mensaje motivador según la nota
    if nota >= 5:
        st.success(f"¡Buen trabajo! Has superado el test con un {nota:.2f}")
    else:
        st.error(f"Nota: {nota:.2f}. ¡Toca repasar un poco más!")

    st.write("")

    if st.button("🔄 Volver al Inicio", use_container_width=True, type="primary"):
        st.session_state.examen_iniciado = False
        st.session_state.pantalla = "menu"
        st.rerun()
