import streamlit as st
from supabase import create_client
import random

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
st.set_page_config(page_title="OpoTests PMM", page_icon="👮‍♂️", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Ranchers&display=swap');
    </style>
    """, unsafe_allow_html=True)

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

# --- 2. ESTILOS CSS ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # Esto evita que la app pete si el archivo no está (opcional)
        st.error(f"No se encontró el archivo {file_name}")

local_css("style.css")

# --- 3. LÓGICA DE NAVEGACIÓN Y ESTADO ---
if "examen_iniciado" not in st.session_state:
    st.session_state.update({
        "examen_iniciado": False, "pantalla": "menu", "sub_pantalla": "inicio",
        "preguntas": [], "indice": 0, "aciertos": 0, "fallos": 0,
        "respuesta_dada": None, "tema_elegido_id": None, "tema_elegido_nombre": ""
    })

def cambiar_vista(pantalla=None, sub=None, reset_examen=False):
    if pantalla: st.session_state.pantalla = pantalla
    if sub: st.session_state.sub_pantalla = sub
    if reset_examen:
        st.session_state.examen_iniciado = False

def volver_atras():
    if st.session_state.pantalla != "menu":
        cambiar_vista("menu", "inicio")
    elif st.session_state.sub_pantalla in ["teoria_opciones", "config_ingles", "config_simulacro"]:
        cambiar_vista(sub="inicio")
    elif st.session_state.sub_pantalla in ["seleccion_tema", "config_examen_tema"]:
        cambiar_vista(sub="teoria_opciones")

# --- 4. FUNCIONES DE DATOS ---
def iniciar_examen(temas_ids, cantidad):
    res = supabase.table("preguntas").select("*").in_("tema_id", temas_ids).execute()
    if res.data:
        lista = res.data
        random.shuffle(lista)
        st.session_state.update({
            "preguntas": lista[:cantidad], "examen_iniciado": True,
            "indice": 0, "aciertos": 0, "fallos": 0, "respuesta_dada": None
        })
        st.rerun()

# --- 5. COMPONENTES VISUALES ---
def render_cabecera():
    if st.session_state.examen_iniciado is not False: return
    col_izq, col_titulo, col_der = st.columns([0.15, 0.7, 0.15])
    with col_izq:
        if st.session_state.pantalla == "menu" and st.session_state.sub_pantalla == "inicio":
            st.button("❓", use_container_width=True)
        else:
            st.button("⬅️", use_container_width=True, on_click=volver_atras)
    with col_titulo:
        titulos = {
            "biblioteca": "BIBLIOTECA", "teoria_opciones": "MODO TEORÍA",
            "seleccion_tema": "TEMAS", "config_examen_tema": "AJUSTES TEST",
            "config_simulacro": "AJUSTES TEST", "config_ingles": "AJUSTES TEST"
        }
        nombre = titulos.get(st.session_state.sub_pantalla, titulos.get(st.session_state.pantalla, "OPOTESTS PMM"))
        st.markdown(f'<div class="titulo-pantalla">{nombre}</div>', unsafe_allow_html=True)
    with col_der: st.button("👤", use_container_width=True)
    st.divider()

# --- 6. FLUJO PRINCIPAL ---
render_cabecera()

# CASO A: EXAMEN EN CURSO
if st.session_state.examen_iniciado is True:
    idx, total = st.session_state.indice, len(st.session_state.preguntas)
    p = st.session_state.preguntas[idx]
    
    st.markdown(f"P: {idx+1}/{total} | ✅ {st.session_state.aciertos} | ❌ {st.session_state.fallos}")
    st.progress((idx + 1) / total)
    st.markdown(f"#### {p['enunciado']}")

    for l in ["A", "B", "C"]:
        txt = p[f'opcion_{l.lower()}']
        if st.session_state.respuesta_dada:
            if l == p['correcta']: txt = f"✅ {txt}"
            elif l == st.session_state.respuesta_dada: txt = f"❌ {txt}"
        
        if st.button(f"{l}) {txt}", key=f"p_{idx}_{l}", use_container_width=True, disabled=st.session_state.respuesta_dada is not None):
            st.session_state.respuesta_dada = l
            st.session_state.preguntas[idx]['respuesta_usuario'] = l 
            if l == p['correcta']: st.session_state.aciertos += 1
            else: st.session_state.fallos += 1
            st.rerun()

    if st.session_state.respuesta_dada:
        st.markdown(f'<div style="background-color:#3e5871;padding:15px;border-radius:10px;border-left:5px solid #3498db;margin-top:20px;">{p.get("explicacion", "")}</div>', unsafe_allow_html=True)
        st.markdown('<div class="espacio-botones">', unsafe_allow_html=True)
        if st.button("Siguiente Pregunta ➔", type="primary", use_container_width=True):
            if idx < total - 1:
                st.session_state.indice += 1
                st.session_state.respuesta_dada = None
            else: st.session_state.examen_iniciado = "FINALIZADO"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# CASO B: RESULTADOS
elif st.session_state.examen_iniciado == "FINALIZADO":
    col_img_1, col_img_2, col_img_3, col_img_4, col_img_5 = st.columns([1, 1, 1, 1, 1])
    with col_img_3:
        # Cargamos la imagen desde la carpeta assets de tu repo
        st.image("assets/trophy.png", use_container_width=True)
    ac, fa = st.session_state.aciertos, st.session_state.fallos
    total = len(st.session_state.preguntas)
    netas = max(0, ac - (fa * 0.33))
    nota = (netas / total * 10) if total > 0 else 0
    
    # Contenedor de métricas personalizadas
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f'''<div class="metric-card metric-aciertos">
            <div class="metric-label">Aciertos</div>
            <div class="metric-value">{ac}</div>
        </div>''', unsafe_allow_html=True)
        
    with c2:
        st.markdown(f'''<div class="metric-card metric-fallos">
            <div class="metric-label">Fallos</div>
            <div class="metric-value">{fa}</div>
        </div>''', unsafe_allow_html=True)
        
    with c3:
        st.markdown(f'''<div class="metric-card metric-nota">
            <div class="metric-label">Nota Final</div>
            <div class="metric-value">{nota:.2f}</div>
        </div>''', unsafe_allow_html=True)
        
    with c4:
        st.markdown(f'''<div class="metric-card metric-netas">
            <div class="metric-label">Netas</div>
            <div class="metric-value">{netas:.2f}</div>
        </div>''', unsafe_allow_html=True)

    # Botones de acción con el aire que definimos antes
    st.markdown('<div class="espacio-botones">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 REVISAR PREGUNTA A PREGUNTA", use_container_width=True): 
            st.session_state.examen_iniciado = "MODO_REVISION"
            st.session_state.indice = 0
            st.rerun()
    with col2:
        if st.button("🔄 FINALIZAR Y VOLVER AL INICIO", use_container_width=True, type="primary"): 
            cambiar_vista(pantalla="menu", sub="inicio", reset_examen=True)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    if (nota == 10):st.balloons()

# CASO C: REVISIÓN
elif st.session_state.examen_iniciado == "MODO_REVISION":
    idx = st.session_state.indice
    p = st.session_state.preguntas[idx]
    user_res = p.get('respuesta_usuario', None)

    st.markdown(f"### Revisando Pregunta {idx+1} de {len(st.session_state.preguntas)}")
    st.info(f"**{p['enunciado']}**")

    for l in ["A", "B", "C"]:
        txt = p[f'opcion_{l.lower()}']
        if l == p['correcta']: st.success(f"{l}) {txt} (Correcta)")
        elif l == user_res: st.error(f"{l}) {txt} (Tu respuesta)")
        else: st.write(f"{l}) {txt}")

    st.markdown(f'<div style="background-color:#3e5871;padding:15px;border-radius:10px;border-left:5px solid #3498db;margin-top:20px;">{p.get("explicacion", "")}</div>', unsafe_allow_html=True)

    # Envolvemos el botón en un div con la clase de CSS
    st.markdown('<div class="espacio-botones">', unsafe_allow_html=True)
    c_p, c_n, c_e = st.columns([0.3, 0.3, 0.4])
    with c_p:
        if st.button("⬅️ Anterior", disabled=(idx == 0), use_container_width=True):
            st.session_state.indice -= 1
            st.rerun()
    with c_n:
        if st.button("Siguiente ➡️", disabled=(idx == len(st.session_state.preguntas)-1), use_container_width=True):
            st.session_state.indice += 1
            st.rerun()
    with c_e:
        if st.button("Volver a Resultados", type="primary", use_container_width=True):
            st.session_state.examen_iniciado = "FINALIZADO"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
# CASO D: MENÚS Y OTROS
elif st.session_state.pantalla == "menu":
    if st.session_state.sub_pantalla == "inicio":
        c1, c2 = st.columns(2)
        if c1.button("📚 TEORÍA", use_container_width=True): 
            cambiar_vista(sub="teoria_opciones")
            st.rerun()
        if c2.button("🇬🇧 INGLÉS", use_container_width=True): 
            st.session_state.tema_elegido_nombre = "Inglés"
            cambiar_vista(sub="config_ingles")
            st.rerun()
        st.write(""); c3, c4 = st.columns(2)
        if c3.button("📖 BIBLIOTECA", use_container_width=True): 
            cambiar_vista(pantalla="biblioteca")
            st.rerun()
        if c4.button("📊 ESTADÍSTICAS", use_container_width=True): st.toast("Próximamente")
    
    elif st.session_state.sub_pantalla == "teoria_opciones":
        c1, c2 = st.columns(2)
        if c1.button("📂 POR TEMAS", use_container_width=True): 
            cambiar_vista(sub="seleccion_tema")
            st.rerun()
        if c2.button("⏱️ SIMULACRO", use_container_width=True): 
            st.session_state.tema_elegido_nombre = "Simulacro"
            cambiar_vista(sub="config_simulacro")
            st.rerun()

    elif st.session_state.sub_pantalla == "seleccion_tema":
        if "temas_seleccionados" not in st.session_state:
            st.session_state.temas_seleccionados = []
        res_t = supabase.table("temas").select("*").neq("id", 1).order("id").execute()
        if res_t.data:
            temas = res_t.data
            total_temas = len(temas)
            mitad = (total_temas + 1) // 2        
            col1, col2 = st.columns(2)
            def toggle_tema(tema_id):
                if tema_id in st.session_state.temas_seleccionados:
                    st.session_state.temas_seleccionados.remove(tema_id)
                else:
                    st.session_state.temas_seleccionados.append(tema_id)
            for i, t in enumerate(temas):
                objetivo_col = col1 if i < mitad else col2
                with objetivo_col:
                    esta_seleccionado = t['id'] in st.session_state.temas_seleccionados
                    label = f"✅ {t['nombre']}" if esta_seleccionado else t['nombre']
                    if st.button(label, key=f"t_{t['id']}", use_container_width=True, type="primary" if esta_seleccionado else "secondary"):
                        toggle_tema(t['id'])
                        st.rerun()
    
            st.divider()
            if st.session_state.temas_seleccionados:
                c1, c2, c3 = st.columns([1, 2, 1])
                with c2:
                    if st.button(f"🚀 LANZAR EXAMEN ({len(st.session_state.temas_seleccionados)} TEMAS)", use_container_width=True):
                        st.session_state.tema_elegido_id = st.session_state.temas_seleccionados
                        st.session_state.tema_elegido_nombre = f"Mix de {len(st.session_state.temas_seleccionados)} Temas"
                        cambiar_vista(sub="config_examen_tema")
                        st.rerun()
            else:
                st.info("Selecciona al menos un tema para continuar")

    elif st.session_state.sub_pantalla in ["config_ingles", "config_simulacro", "config_examen_tema"]:
        st.write(f"Configurando: **{st.session_state.tema_elegido_nombre}**")
        num = st.select_slider("Preguntas:", options=[10, 20, 40, 80, 100], value=10)
        if st.button("🚀 COMENZAR", type="primary", use_container_width=True):
            if st.session_state.sub_pantalla == "config_ingles": ids = [1]
            elif st.session_state.sub_pantalla == "config_simulacro":
                ids = [r['id'] for r in supabase.table("temas").select("id").neq("id", 1).execute().data]
            else: 
                if isinstance(st.session_state.tema_elegido_id, list):
                    ids = st.session_state.tema_elegido_id
                else:
                    ids = [st.session_state.tema_elegido_id]
            iniciar_examen(ids, num)

elif st.session_state.pantalla == "biblioteca":
    for ley in supabase.table("biblioteca").select("*").order("orden").execute().data:
        with st.container(border=True):
            ct, cb = st.columns([0.7, 0.3])
            ct.write(f"**{ley['name']}**"); cb.link_button("📄 PDF", ley['url_pdf'], use_container_width=True)
