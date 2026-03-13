import streamlit as st
from supabase import create_client
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="OpoTests PMM - Web", page_icon="👮‍♂️", layout="wide")

# --- CONEXIÓN A SUPABASE ---
# --- CONFIGURACIÓN ---
URL= "https://viglgksnpajdgpfprmqg.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpZ2xna3NucGFqZGdwZnBybXFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDkzNDcsImV4cCI6MjA4ODkyNTM0N30.k2o2KzYnRvg3fSjMA5fCvn2-VAJVZMJiUW1_UKFNZiA"

supabase = create_client(URL, KEY)

# --- ESTILOS ESENCIALES (El resto ya lo hace el config.toml) ---
st.markdown("""
    <style>
    .stApp { background-color: #2c3e50; color: white; }
    
    /* 1. BOTONES ORIGINALES (Antes de pulsar) */
    div.stButton > button {
        height: 60px !important;
        width: 100% !important;
        font-weight: 500 !important;
        font-size: 18px !important;
        border-radius: 10px !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        background-color: #34495e !important;
        transition: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important; /* Centrado del botón */
    }

    /* 2. BLOQUES DE RESPUESTA (Después de pulsar) */
    .respuesta-block {
        height: 60px;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center; /* Centrado horizontal */
        text-align: center;      /* Centrado del texto interno */
        padding: 10px 20px;
        border-radius: 10px;
        margin-bottom: 12px;
        font-weight: 500 !important;
        font-size: 18px !important;
        border: 1px solid rgba(255,255,255,0.1);
        box-sizing: border-box;
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

# --- PANTALLA 1: MENÚ PRINCIPAL (CONFIGURACIÓN) ---
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
            
            st.write(f" *Temas listos: {len(temas_seleccionados_ids)}*")
            
            st.markdown("### 📝 Número de preguntas")
            cantidad = st.select_slider("Cantidad:", options=[10, 20, 40, 60, 80, 100], value=20)
            
            st.write("")
            if st.button("🚀 INICIAR EXAMEN", type="primary", use_container_width=True):
                if not temas_seleccionados_ids:
                    st.warning("Selecciona al menos un tema.")
                else:
                    iniciar_examen(temas_seleccionados_ids, cantidad)
                    st.rerun()

    except Exception as e:
        st.error(f"Error de conexión: {e}")

# --- PANTALLA 2: EL EXAMEN ---
elif st.session_state.examen_iniciado is True:
    idx = st.session_state.indice
    p = st.session_state.preguntas[idx]
    total = len(st.session_state.preguntas)

    # Panel de Stats
    st.markdown(f"""
        <div style="background-color: #34495e; padding: 12px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
            <b>Pregunta {idx+1}/{total}</b> | ✅ {st.session_state.aciertos} | ❌ {st.session_state.fallos}
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<h3 style='text-align: center; margin-bottom: 30px;'>{p['enunciado']}</h3>", unsafe_allow_html=True)

    # Bucle de Respuestas Reparado y Centrado
    _, col_central, _ = st.columns([0.05, 0.9, 0.05])
    
    with col_central:
        for letra in ["A", "B", "C"]:
            texto_opcion = f"{letra}) {p[f'opcion_{letra.lower()}']}"
            
            # CASO A: Aún no ha respondido (Botones Normales de Streamlit)
            if st.session_state.respuesta_dada is None:
                if st.button(texto_opcion, key=f"btn_{letra}_{idx}", use_container_width=True):
                    st.session_state.respuesta_dada = letra
                    if letra == p['correcta']:
                        st.session_state.aciertos += 1
                    else:
                        st.session_state.fallos += 1
                    st.rerun() # Esto recarga y activa el CASO B
            
            # CASO B: Ya respondió (Dibujamos bloques HTML uniformes y coloreados)
            else:
                # Aquí es donde aplicamos el color de fondo DINÁMICO
                color_fondo = "#34495e" # Gris azulado por defecto (idéntico al botón sin hover)
                
                if letra == p['correcta']:
                    color_fondo = "#27ae60" # VERDE sólido
                elif letra == st.session_state.respuesta_dada:
                    color_fondo = "#c0392b" # ROJO sólido
                
                # Pintamos el bloque HTML uniforme
                st.markdown(f"""
                    <div class="respuesta-block" style="background-color: {color_fondo};">
                        {texto_opcion}
                    </div>
                """, unsafe_allow_html=True)

    if st.session_state.respuesta_dada:
        st.markdown(f"""
            <div style="background-color: #1a252f; padding: 20px; border-radius: 10px; border-left: 5px solid #3498db; margin: 25px 0;">
                <small style="color: #3498db;"><b>💡 EXPLICACIÓN</b></small><br>
                <div style="margin-top: 10px;">{p['explicacion'] if p.get('explicacion') else 'Sin explicación.'}</div>
            </div>
        """, unsafe_allow_html=True)
        
        _, col_btn, _ = st.columns([0.2, 0.6, 0.2])
        with col_btn:
            if st.button("Siguiente ➔", type="primary", use_container_width=True):
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
