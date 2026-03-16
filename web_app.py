import streamlit as st
from supabase import create_client
import random

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="OpoTests PMM", page_icon="👮‍♂️", layout="wide")

# --- 2. CONEXIÓN A SUPABASE ---
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- 3. ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #2c3e50; color: white; }
    [data-testid="stHorizontalBlock"] { align-items: center !important; }
    
    .titulo-pantalla {
        text-align: center;
        margin: 0 !important;
        letter-spacing: 2px;
        color: white;
        font-weight: 700;
        font-size: 26px;
        text-transform: uppercase;
    }

    div.stButton > button {
        min-height: 70px !important;
        font-size: 18px !important;
        border-radius: 12px !important;
        transition: 0.3s;
        background-color: #34495e;
        color: white;
        border: 1px solid #465d75;
    }
    
    div.stButton > button:hover { border-color: #3498db; color: #3498db; }
    [data-testid="stMetricValue"] { font-size: 30px !important; color: #3498db !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if "examen_iniciado" not in st.session_state:
    st.session_state.examen_iniciado = False
    st.session_state.pantalla = "menu"
    st.session_state.sub_pantalla = "inicio"
    st.session_state.preguntas = []
    st.session_state.indice = 0
    st.session_state.aciertos = 0
    st.session_state.fallos = 0
    st.session_state.respuesta_dada = None
    st.session_state.tema_elegido_id = None
    st.session_state.tema_elegido_nombre = ""

# --- 5. FUNCIONES ---
def iniciar_examen(temas_ids, cantidad):
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

# --- 6. CABECERA ---
if st.session_state.examen_iniciado is False:
    col_izq, col_titulo, col_der = st.columns([0.15, 0.7, 0.15])
    with col_izq:
        if st.session_state.pantalla == "menu" and st.session_state.sub_pantalla == "inicio":
            st.button("❓", use_container_width=True, key="h_ayuda")
        else:
            if st.button("⬅️", use_container_width=True, key="h_volver"):
                if st.session_state.pantalla != "menu":
                    st.session_state.pantalla = "menu"
                    st.session_state.sub_pantalla = "inicio"
                elif st.session_state.sub_pantalla in ["teoria_opciones", "config_ingles", "config_simulacro"]:
                    st.session_state.sub_pantalla = "inicio"
                elif st.session_state.sub_pantalla in ["seleccion_tema", "config_examen_tema"]:
                    st.session_state.sub_pantalla = "teoria_opciones"
                st.rerun()
    with col_titulo:
        n_pan = "OPOTESTS PMM"
        if st.session_state.pantalla == "biblioteca": n_pan = "BIBLIOTECA"
        elif st.session_state.sub_pantalla == "teoria_opciones": n_pan = "MODO TEORÍA"
        elif st.session_state.sub_pantalla == "seleccion_tema": n_pan = "TEMARIOS"
        elif st.session_state.sub_pantalla in ["config_examen_tema", "config_simulacro", "config_ingles"]: n_pan = "AJUSTES TEST"
        st.markdown(f'<div class="titulo-pantalla">{n_pan}</div>', unsafe_allow_html=True)
    with col_der:
        st.button("👤", use_container_width=True, key="h_perfil")
    st.divider()

# --- 7. FLUJO DE PANTALLAS ---
if st.session_state.examen_iniciado is False:
    if st.session_state.pantalla == "menu":
        if st.session_state.sub_pantalla == "inicio":
            c1, c2 = st.columns(2)
            if c1.button("📚 TEORÍA", use_container_width=True):
                st.session_state.sub_pantalla = "teoria_opciones"; st.rerun()
            if c2.button("🇬🇧 INGLÉS", use_container_width=True):
                st.session_state.tema_elegido_nombre = "Inglés"; st.session_state.sub_pantalla = "config_ingles"; st.rerun()
            st.write(""); c3, c4 = st.columns(2)
            if c3.button("📖 BIBLIOTECA", use_container_width=True):
                st.session_state.pantalla = "biblioteca"; st.rerun()
            if c4.button("📊 ESTADÍSTICAS", use_container_width=True): st.toast("Próximamente")

        elif st.session_state.sub_pantalla == "teoria_opciones":
            c1, c2 = st.columns(2)
            if c1.button("📂 POR TEMAS", use_container_width=True):
                st.session_state.sub_pantalla = "seleccion_tema"; st.rerun()
            if c2.button("⏱️ SIMULACRO", use_container_width=True):
                st.session_state.tema_elegido_nombre = "Simulacro"; st.session_state.sub_pantalla = "config_simulacro"; st.rerun()

        elif st.session_state.sub_pantalla == "seleccion_tema":
            res_t = supabase.table("temas").select("*").neq("id", 1).order("id").execute()
            if res_t.data:
                cols = st.columns(2)
                for i, t in enumerate(res_t.data):
                    with cols[i % 2]:
                        if st.button(t['nombre'], key=f"t_{t['id']}", use_container_width=True):
                            st.session_state.tema_elegido_id = t['id']; st.session_state.tema_elegido_nombre = t['nombre']
                            st.session_state.sub_pantalla = "config_examen_tema"; st.rerun()

        elif st.session_state.sub_pantalla in ["config_ingles", "config_simulacro", "config_examen_tema"]:
            st.write(f"Configurando: **{st.session_state.tema_elegido_nombre}**")
            num = st.select_slider("Preguntas:", options=[5, 10, 20, 50], value=10)
            if st.button("🚀 COMENZAR", type="primary", use_container_width=True):
                if st.session_state.sub_pantalla == "config_ingles": ids = [1]
                elif st.session_state.sub_pantalla == "config_simulacro":
                    ids = [r['id'] for r in supabase.table("temas").select("id").neq("id", 1).execute().data]
                else: ids = [st.session_state.tema_elegido_id]
                iniciar_examen(ids, num); st.rerun()

    elif st.session_state.pantalla == "biblioteca":
        for ley in supabase.table("biblioteca").select("*").order("orden").execute().data:
            with st.container(border=True):
                ct, cb = st.columns([0.7, 0.3])
                ct.write(f"**{ley['name']}**")
                cb.link_button("📄 PDF", ley['url_pdf'], use_container_width=True)

# --- 8. EXAMEN ---
elif st.session_state.examen_iniciado is True:
    idx = st.session_state.indice
    p = st.session_state.preguntas[idx]
    st.markdown(f"P: {idx+1}/{len(st.session_state.preguntas)} | ✅ {st.session_state.aciertos} | ❌ {st.session_state.fallos}")
    st.markdown(f"#### {p['enunciado']}")
    for l in ["A", "B", "C"]:
        txt = p[f'opcion_{l.lower()}']
        if st.session_state.respuesta_dada:
            if l == p['correcta']: txt = f"✅ {txt}"
            elif l == st.session_state.respuesta_dada: txt = f"❌ {txt}"
        if st.button(f"{l}) {txt}", key=f"p_{idx}_{l}", use_container_width=True, disabled=st.session_state.respuesta_dada is not None):
            st.session_state.respuesta_dada = l
            if l == p['correcta']: st.session_state.aciertos += 1
            else: st.session_state.fallos += 1
            st.rerun()
    if st.session_state.respuesta_dada:
        st.info(p.get('explicacion', ''))
        if st.button("Siguiente ➔", use_container_width=True):
            if idx < len(st.session_state.preguntas) - 1:
                st.session_state.indice += 1; st.session_state.respuesta_dada = None
            else: st.session_state.examen_iniciado = "FINALIZADO"
            st.rerun()

# --- 9. FINAL ---
elif st.session_state.examen_iniciado == "FINALIZADO":
    st.balloons(); st.markdown("### RESULTADOS")
    st.metric("Nota", f"{(st.session_state.aciertos - st.session_state.fallos*0.33):.2f}")
    if st.button("Volver"):
        st.session_state.examen_iniciado = False; st.session_state.pantalla = "menu"; st.session_state.sub_pantalla = "inicio"; st.rerun()
