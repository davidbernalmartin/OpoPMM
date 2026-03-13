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
    .stApp { background-color: #2c3e50; color: white; }
    
    /* El botón: mínimo 2 líneas, crece si es necesario */
    div.stButton > button {
        min-height: 85px !important; 
        height: auto !important; /* Permite que crezca */
        width: 100% !important;
        font-size: 18px !important;
        border-radius: 10px !important;
        padding: 10px 15px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: normal !important; /* Fuerza el salto de línea del texto */
        word-wrap: break-word !important;
    }

    /* El contenedor del icono: debe estirarse igual que el botón */
    .icon-container {
        display: flex;
        align-items: center; /* Mantiene el icono centrado verticalmente siempre */
        justify-content: center;
        min-height: 85px; 
        height: 100%; /* Se acopla a la altura de la fila */
    }

    .icon-style {
        font-size: 35px;
        line-height: 1;
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE ESTADO ---
if "examen_iniciado" not in st.session_state:
    st.session_state.examen_iniciado = False
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

# --- PANTALLA 1: CONFIGURACIÓN ---
if not st.session_state.examen_iniciado:
    st.markdown("""
        <div style="background-color: #34495e; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 30px; border-bottom: 5px solid #3498db;">
            <h1 style='margin:0; color: white;'>SISTEMA PMM CLOUD</h1>
            <p style='margin:0; color: #bdc3c7;'>Panel de Configuración</p>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        res_temas = supabase.table("temas").select("id, nombre").order("id").execute().data
        _, col_config, _ = st.columns([0.1, 0.8, 0.1])
        with col_config:
            st.markdown("### 📚 Selecciona los Temas")
            with st.container(height=300, border=True):
                temas_seleccionados_ids = []
                seleccionar_todos = st.checkbox("Marcar todos los temas", value=True)
                st.divider()
                for t in res_temas:
                    if st.checkbox(t['nombre'], value=seleccionar_todos, key=f"check_{t['id']}"):
                        temas_seleccionados_ids.append(t['id'])
            
            cantidad = st.select_slider("Cantidad de preguntas:", options=[10, 20, 40, 60, 80, 100], value=20)
            if st.button("🚀 INICIAR EXAMEN", type="primary", use_container_width=True):
                if not temas_seleccionados_ids:
                    st.warning("Selecciona al menos un tema.")
                else:
                    iniciar_examen(temas_seleccionados_ids, cantidad)
                    st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# --- PANTALLA 2: EL EXAMEN ---
elif st.session_state.examen_iniciado is True:
    idx = st.session_state.indice
    p = st.session_state.preguntas[idx]
    total = len(st.session_state.preguntas)

    st.markdown(f"""
        <div style="background-color: #34495e; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
            <b>Pregunta {idx+1}/{total}</b> | ✅ {st.session_state.aciertos} | ❌ {st.session_state.fallos}
        </div>
    """, unsafe_allow_html=True)

    # Enunciado con fuente ajustada y mejor espaciado
    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 35px; padding: 0 20px;'>
            <h3 style='font-size: 20px !important; font-weight: 500; line-height: 1.4; color: #ecf0f1;'>
                {p['enunciado']}
            </h3>
        </div>
    """, unsafe_allow_html=True)

    _, col_central, _ = st.columns([0.05, 0.9, 0.05])
    
    with col_central:
        for letra in ["A", "B", "C"]:
            texto_opcion = f"{letra}) {p[f'opcion_{letra.lower()}']}"
            col_izq, col_btn_resp, col_der = st.columns([0.15, 0.7, 0.15])
            
            with col_btn_resp:
                if st.button(texto_opcion, key=f"btn_{letra}_{idx}", use_container_width=True, disabled=st.session_state.respuesta_dada is not None):
                    st.session_state.respuesta_dada = letra
                    if letra == p['correcta']:
                        st.session_state.aciertos += 1
                    else:
                        st.session_state.fallos += 1
                    st.rerun()

            with col_izq:
                if st.session_state.respuesta_dada:
                    # Envolvemos el icono en un div que ocupa todo el alto
                    icon = "✅" if letra == p['correcta'] else "❌"
                    if letra == p['correcta'] or letra == st.session_state.respuesta_dada:
                        st.markdown(f"""
                            <div class="icon-container">
                                <span class="icon-style">{icon}</span>
                            </div>
                        """, unsafe_allow_html=True)

    if st.session_state.respuesta_dada:
        st.markdown(f"""
            <div style="background-color: #1a252f; padding: 20px; border-radius: 10px; border-left: 5px solid #3498db; margin: 25px 0;">
                <small style="color: #3498db;"><b>💡 EXPLICACIÓN</b></small><br>
                <div style="margin-top: 10px;">{p['explicacion'] if p.get('explicacion') else 'Sin explicación.'}</div>
            </div>
        """, unsafe_allow_html=True)
        
        with col_der:
            if st.button("Siguiente Pregunta ➔", type="primary", use_container_width=True):
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
    st.markdown("<h1 style='text-align: center;'>Resultado</h1>", unsafe_allow_html=True)
    total = len(st.session_state.preguntas)
    netos = max(0, st.session_state.aciertos - (st.session_state.fallos * 0.33))
    nota = (netos / total * 10) if total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Aciertos", st.session_state.aciertos)
    col2.metric("Fallos", st.session_state.fallos)
    col3.metric("Nota", f"{nota:.2f}")

    if st.button("Volver al Inicio", use_container_width=True):
        st.session_state.examen_iniciado = False
        st.rerun()
