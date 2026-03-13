import streamlit as st
from supabase import create_client
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="OpoTests PMM - Web", page_icon="👮‍♂️", layout="wide")

# --- CONEXIÓN A SUPABASE ---
# --- CONFIGURACIÓN ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(URL, KEY)

# --- ESTILOS ESENCIALES (El resto ya lo hace el config.toml) ---
st.markdown("""
    <style>
    /* ... (tus otros estilos) ... */

    .icon-style {
        font-size: 32px; /* Un pelín más pequeño para que no "tire" de la línea */
        display: flex;
        align-items: center; /* Centrado vertical */
        justify-content: center; /* Centrado horizontal en su columna */
        height: 60px; /* Misma altura que el min-height del botón */
        line-height: 60px;
        margin-top: 2px; /* Pequeño ajuste fino para nivelar con el texto del botón */
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

    # 1. Definimos el espacio central
    _, col_central, _ = st.columns([0.05, 0.9, 0.05])
    
    with col_central:
        for letra in ["A", "B", "C"]:
            texto_opcion = f"{letra}) {p[f'opcion_{letra.lower()}']}"
            
            # Creamos 3 columnas: [Icono vacío (izq), Botón (centro), Icono (der)]
            # Al poner 0.15 a ambos lados, el botón queda perfectamente centrado
            col_izq, col_btn_resp, col_der = st.columns([0.15, 0.7, 0.15])
            
            with col_btn_resp:
                if st.button(texto_opcion, key=f"btn_{letra}_{idx}", use_container_width=True, disabled=st.session_state.respuesta_dada is not None):
                    st.session_state.respuesta_dada = letra
                    if letra == p['correcta']:
                        st.session_state.aciertos += 1
                    else:
                        st.session_state.fallos += 1
                    st.rerun()

            with col_der:
                if st.session_state.respuesta_dada:
                    if letra == p['correcta']:
                        # Usamos la clase corregida
                        st.markdown('<div class="icon-style">✅</div>', unsafe_allow_html=True)
                    elif letra == st.session_state.respuesta_dada and letra != p['correcta']:
                        st.markdown('<div class="icon-style">❌</div>', unsafe_allow_html=True)

# --- MOSTRAR EXPLICACIÓN Y BOTÓN SIGUIENTE SOLO DESPUÉS DE RESPONDER ---
    if st.session_state.respuesta_dada:
        # 1. El cuadro de explicación elegante
        st.markdown(f"""
            <div style="background-color: #1a252f; padding: 20px; border-radius: 10px; border-left: 5px solid #3498db; margin: 25px 0;">
                <small style="color: #3498db;"><b>💡 EXPLICACIÓN</b></small><br>
                <div style="margin-top: 10px;">{p['explicacion'] if p.get('explicacion') else 'Sin explicación.'}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # 2. El botón de Siguiente centrado
        _, col_btn, _ = st.columns([0.2, 0.6, 0.2])
        with col_btn:
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
