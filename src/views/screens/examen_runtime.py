from __future__ import annotations
from typing import Callable
import streamlit as st
from src.models.examen import Examen
import time

# --- DIÁLOGO 2: EDICIÓN / CREACIÓN ---
@st.dialog("✏️ Editor de Pregunta", width="large")
def modal_editar_pregunta(pregunta, supabase):
    """Muestra el formulario de edición usando el componente existente."""
    from src.views.components.pregunta_form import renderizar_formulario_edicion_pregunta
    
    res_temas = supabase.table("temas").select("id, nombre").execute()
    temas_db = res_temas.data if res_temas.data else []
    temas_nombres = [t["nombre"] for t in temas_db]
    temas_dict = {t["nombre"]: t["id"] for t in temas_db}
    id_a_nombre = {t["id"]: t["nombre"] for t in temas_db}

    pregunta["tema_nombre"] = id_a_nombre.get(pregunta.get("tema_id"), "")
    st.subheader("Edición de Pregunta" if pregunta.get('id') else "Nueva Pregunta")
    
    # Renderizamos tu formulario
    f_enun, f_exp, f_a, f_b, f_c, f_corr, f_tema_nom = renderizar_formulario_edicion_pregunta(pregunta, temas_nombres)
    
    st.divider()
    col_g, col_c = st.columns(2)
    
    if col_g.button("💾 GUARDAR CAMBIOS", type="primary", width='stretch'):
        data_save = {
            "enunciado": f_enun,
            "explicacion": f_exp,
            "opcion_a": f_a,
            "opcion_b": f_b,
            "opcion_c": f_c,
            "correcta": f_corr,
            "tema_id": temas_dict.get(f_tema_nom)
        }
        
        with st.spinner("Sincronizando con base de datos..."):
            try:
                # 1. Actualización en Supabase
                supabase.table("preguntas").update(data_save).eq("id", pregunta["id"]).execute()
                
                # 2. ACTUALIZACIÓN EN CALIENTE (La clave del éxito)
                # Como 'pregunta' es una referencia al objeto dentro de st.session_state.preguntas_examen,
                # al usar .update() estamos modificando la lista real que usa el runtime.
                pregunta.update(data_save)
                pregunta["tema_nombre"] = f_tema_nom # Sincronizamos también el nombre para el formulario
                
                st.success("✅ ¡Base de datos y vista sincronizadas!")
                time.sleep(0.8)
                st.rerun() # Esto recargará la pantalla de revisión con los datos ya actualizados
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    if col_c.button("❌ CANCELAR", width='stretch'):
        st.rerun()

def render_examen_runtime(
    *,
    titulo: str,
    lista_preguntas: list[dict],
    guardar_resultado_examen: Callable[[list[dict], dict[int, str], str, int], tuple[float, int, int]],
    limpiar_estado_maestro: Callable[[], None],
    supabase: Any,
) -> None:
    st.markdown(f'<div class="titulo-pantalla">{titulo}</div>', unsafe_allow_html=True)
    # 1. MODO REVISIÓN
    if st.session_state.get("ver_revision", False):
        _render_revision(lista_preguntas, supabase)

    # 2. MODO RESULTADO FINAL
    elif st.session_state.examen_finalizado:
        _render_resultado_final(lista_preguntas, limpiar_estado_maestro)

    # 3. MODO EXAMEN ACTIVO
    else:
        _render_pregunta_activa(lista_preguntas, guardar_resultado_examen, titulo)

# --- BLOQUES DE RENDERIZADO (Lógica Refactorizada) ---

def _render_revision(lista_preguntas, supabase):
    idx = st.session_state.get("indice_revision", 0)
    p = lista_preguntas[idx]
    resp_u = st.session_state.respuestas_usuario.get(idx)
    dudosas = st.session_state.get("preguntas_dudosas", {})
    es_dudosa = dudosas.get(idx, False) or dudosas.get(str(idx), False)
    correcta = p.get('correcta', 'A').upper()

    st.progress((idx + 1) / len(lista_preguntas), text=f"Revisando {idx + 1} de {len(lista_preguntas)}")

    # --- LÓGICA DE COLORES SEMÁNTICOS ---
    # Definimos el esquema de colores basado en tus 4 estados
    if es_dudosa:
        border_color = "#facc15"
        label_estado = "🤔 MARCADA COMO DUDA"
    elif resp_u is None:
        border_color = "#cbd5e1"
        label_estado = "⚪ NO CONTESTADA"
    elif resp_u == correcta:
        border_color = "#22c55e"
        label_estado = "✅ PREGUNTA ACERTADA"
    else:
        border_color = "#ef4444"
        label_estado = "❌ PREGUNTA FALLADA"

    # --- RENDERIZADO DEL ENUNCIADO CON FONDO DINÁMICO ---
    st.markdown(f"""
        <div class="enunciado-container" style="
            border-left: 5px solid {border_color};
            padding: 1.5rem; 
            border-radius: 10px; 
            margin-bottom: 20px;
            ">
            <div style="font-size: 0.75rem; font-weight: bold; margin-bottom: 8px; opacity: 0.7; letter-spacing: 0.05em;">
                {label_estado}
            </div>
            <div style="font-size: 1.1rem; line-height: 1.5;">
                {p['enunciado']}
            </div>
        </div>
    """, unsafe_allow_html=True)

    for letra, texto in [("A", p["opcion_a"]), ("B", p["opcion_b"]), ("C", p["opcion_c"])]:
        # Lógica de colores idéntica a la original
        if letra == p["correcta"]:
            st.markdown(f'<div class="opcion-revision" style="border-left-color: #2ecc71; background: rgba(46,204,113,0.15); font-weight: bold;">{letra}) {texto} <span style="color:#2ecc71;">(Correcta)</span></div>', unsafe_allow_html=True)
        elif letra == resp_u:
            st.markdown(f'<div class="opcion-revision" style="border-left-color: #e74c3c; background: rgba(231,76,60,0.15);">{letra}) {texto} <span style="color:#e74c3c;">(Tu elección)</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="opcion-revision" style="color: #bdc3c7;">{letra}) {texto}</div>', unsafe_allow_html=True)

    st.write("---")
    # Explicación
    exp = p.get("explicacion", "")
    if exp and str(exp).strip():
        st.markdown(f'<div class="explicacion-container"><p style="color:#0891B2; font-weight:bold;">💡 EXPLICACIÓN</p>{exp}</div>', unsafe_allow_html=True)
        st.write("---")

    # Navegación horizontal (Replica tu diseño favorito)
    nav = st.container(horizontal=True)
    with nav:
        if idx > 0 and st.button("⬅️ ANTERIOR", key="rev_p", width='stretch'):
            st.session_state.indice_revision -= 1
            st.rerun()
        
        txt_volver = "VOLVER AL HISTORIAL" if st.session_state.get("sub_pantalla") == "repaso_historial" else "VOLVER AL RESUMEN"
        if st.button(txt_volver, width='stretch'):
            st.session_state.ver_revision = False
            if st.session_state.get("sub_pantalla") == "repaso_historial":
                st.session_state.sub_pantalla = "historial"
            st.rerun()

        if idx < len(lista_preguntas) - 1 and st.button("SIGUIENTE ➡️", key="rev_n", width='stretch'):
            st.session_state.indice_revision += 1
            st.rerun()
        
        if st.session_state.get("user_role") == "admin":
            if st.button("🛠️ Modificar esta pregunta", use_container_width=True):
                modal_editar_pregunta(p, supabase)

def _render_resultado_final(lista_preguntas, limpiar_estado_maestro):
    # --- 1. LÓGICA DE CÁLCULO (Escenario REAL) ---
    total = len(lista_preguntas)
    resps = st.session_state.respuestas_usuario
    dudas = st.session_state.get("preguntas_dudosas", {})
    
    # Cálculo Real (Todo lo respondido)
    aciertos_r = sum(1 for i, p in enumerate(lista_preguntas) if resps.get(i) == p["correcta"])
    fallos_r = sum(1 for i, p in enumerate(lista_preguntas) if resps.get(i) and resps.get(i) != p["correcta"])
    res_real = Examen(total=total, aciertos=aciertos_r, fallos=fallos_r)
    
    # --- 2. LÓGICA DE CÁLCULO (Escenario CONSERVADOR) ---
    # Si marcó duda, lo tratamos como blanco independientemente de si acertó o falló
    aciertos_c = sum(1 for i, p in enumerate(lista_preguntas) if resps.get(i) == p["correcta"] and not dudas.get(i))
    fallos_c = sum(1 for i, p in enumerate(lista_preguntas) if resps.get(i) and resps.get(i) != p["correcta"] and not dudas.get(i))
    res_cons = Examen(total=total, aciertos=aciertos_c, fallos=fallos_c)
    
    # --- 3. INTERFAZ VISUAL ---
    color_real = "#2ecc71" if res_real.nota_sobre_diez >= 5 else "#e74c3c"
    st.markdown(f'<h4 style="text-align:center; color:{color_real};">{"¡ENHORABUENA!" if res_real.nota_sobre_diez >= 5 else "SIGUE INTENTÁNDOLO"}</h4>', unsafe_allow_html=True)
    
    nav = st.container(horizontal=True)
    with nav:
        st.markdown(f"""
            <div class="tarjeta-nota-final" style="background:rgba(46,204,113,0.05); border: 2px solid {color_real};">
                <p style="margin:0; font-size:0.7rem; color:#666;">NOTA REAL (sin riesgo)</p>
                <div class="nota-final"><p style="color:{color_real}">{res_cons.nota_sobre_diez:.2f}</p></div>
                <p style="margin:0; font-size:0.8rem;">✅: {aciertos_r} | ❌: {fallos_r} | ⚪: {res_real.blancos} | 🎯: {res_real.netas:.2f}</p>
            </div>
        """, unsafe_allow_html=True)
        
        diff = res_real.nota_sobre_diez - res_cons.nota_sobre_diez
        color_diff = "#2ecc71" if diff >= 0 else "#e74c3c"
        st.markdown(f"""
            <div class="tarjeta-nota-final" style="background:rgba(189,195,199,0.1); border: 2px dotted #bdc3c7;">
                <p style="margin:0; font-size:0.7rem; color:#666;">NOTA CON RIESGO</p>
                <div class="nota-final"><p style="color:#7f8c8d">{res_real.nota_sobre_diez:.2f}</p></div>
                <p style="margin:0; font-size:0.8rem; color:{color_diff};">
                    {"▲ +" if diff >= 0 else "▼ "}{diff:.2f} pts por riesgo
                </p>
            </div>
        """, unsafe_allow_html=True)
    botonera = st.container(horizontal=True)
    with botonera:
        if st.button("🔍 REVISAR PREGUNTAS", width='stretch'):
            st.session_state.ver_revision = True
            st.session_state.indice_revision = 0
            st.rerun()
        if st.button("🏁 SALIR AL MENÚ", width='stretch', type="primary"):
            limpiar_estado_maestro()
            st.session_state.sub_pantalla = "seleccion_tema"
            st.rerun()

def _render_pregunta_activa(lista_preguntas, guardar_resultado_examen, titulo): 
    
    idx = st.session_state.indice_pregunta
    p = lista_preguntas[idx]
    
    st.progress((idx + 1) / len(lista_preguntas), text=f"Pregunta {idx + 1} de {len(lista_preguntas)}")
    st.markdown(f'<div class="enunciado-container">{p['enunciado']}</div>', unsafe_allow_html=True)

    res_actual = st.session_state.respuestas_usuario.get(idx)
    letras = ["A", "B", "C"]
    
    seleccion = st.radio(
        "Selecciona respuesta:", letras,
        format_func=lambda x: f"{x}) {p[f'opcion_{x.lower()}']}",
        index=letras.index(res_actual) if res_actual in letras else None,
        key=f"r_{idx}"
    )
    if seleccion: st.session_state.respuestas_usuario[idx] = seleccion
    # Inicializamos el estado de dudas si no existe
    if "preguntas_dudosas" not in st.session_state:
        st.session_state.preguntas_dudosas = {}

    # Usamos st.toggle (disponible en versiones recientes) para un look más moderno
    # Si tu versión es antigua, puedes usar st.checkbox
    es_dudosa = st.toggle(
        "❔ Dudosa", 
        value=st.session_state.preguntas_dudosas.get(idx, False),
        key=f"duda_{idx}",
        help="Marca esta casilla si no estás seguro. Calcularemos tu nota simulando que la dejas en blanco."
    )
    
    # Guardamos el estado
    st.session_state.preguntas_dudosas[idx] = es_dudosa

    # Opcional: un pequeño aviso visual si está marcada
    if es_dudosa:
        st.warning("💡 Pregunta marcada para el análisis de riesgo.")

    st.write("---")
    nav = st.container(horizontal=True)
    with nav:
        # Botón Anterior
        btn_ant = st.button("⬅️ Anterior", width='stretch', disabled=(idx == 0))
        if btn_ant:
            st.session_state.indice_pregunta -= 1
            st.rerun()

        # Botón Siguiente / Finalizar
        es_ultima = (idx == len(lista_preguntas) - 1)
        txt_sig = "🏁 Finalizar" if es_ultima else "Siguiente ➡️"
        if st.button(txt_sig, width='stretch', type="primary"):
            if es_ultima:
                with st.spinner("Registrando resultados en el sistema..."):
                    segundos_totales = 0
                    if "inicio_examen" in st.session_state:
                        segundos_totales = int(time.time() - st.session_state.inicio_examen)
                    guardar_resultado_examen(lista_preguntas, st.session_state.respuestas_usuario, titulo, segundos_totales)                
                st.session_state.examen_finalizado = True
                if "inicio_examen" in st.session_state:
                    del st.session_state.inicio_examen
            else:
                st.session_state.indice_pregunta += 1
            st.rerun()