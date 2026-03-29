from __future__ import annotations
from typing import Callable
import streamlit as st
from src.models.examen import Examen

def render_examen_runtime(
    *,
    titulo: str,
    lista_preguntas: list[dict],
    guardar_resultado_examen: Callable[[list[dict], dict[int, str], str], tuple[float, int, int]],
    limpiar_estado_maestro: Callable[[], None],
) -> None:
    st.markdown(f'<div class="titulo-pantalla">{titulo}</div>', unsafe_allow_html=True)
    
    # 1. MODO REVISIÓN
    if st.session_state.get("ver_revision", False):
        _render_revision(lista_preguntas)

    # 2. MODO RESULTADO FINAL
    elif st.session_state.examen_finalizado:
        _render_resultado_final(lista_preguntas, limpiar_estado_maestro)

    # 3. MODO EXAMEN ACTIVO
    else:
        _render_pregunta_activa(lista_preguntas)

# --- BLOQUES DE RENDERIZADO (Lógica Refactorizada) ---

def _render_revision(lista_preguntas):
    idx = st.session_state.get("indice_revision", 0)
    p = lista_preguntas[idx]
    resp_u = st.session_state.respuestas_usuario.get(idx)
    
    st.progress((idx + 1) / len(lista_preguntas), text=f"Revisando {idx + 1} de {len(lista_preguntas)}")
    st.markdown(f"#### {p['enunciado']}")

    for letra, texto in [("A", p["opcion_a"]), ("B", p["opcion_b"]), ("C", p["opcion_c"])]:
        # Lógica de colores idéntica a la original
        if letra == p["correcta"]:
            st.markdown(f'<div class="opcion-revision" style="border-left-color: #2ecc71; background: rgba(46,204,113,0.15); font-weight: bold;">{letra}) {texto} <span style="color:#2ecc71;">(Correcta)</span></div>', unsafe_allow_html=True)
        elif letra == resp_u:
            st.markdown(f'<div class="opcion-revision" style="border-left-color: #e74c3c; background: rgba(231,76,60,0.15);">{letra}) {texto} <span style="color:#e74c3c;">(Tu elección)</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="opcion-revision" style="color: #bdc3c7;">{letra}) {texto}</div>', unsafe_allow_html=True)

    # Explicación
    exp = p.get("explicacion", "")
    if exp and str(exp).strip():
        st.markdown(f'<div class="explicacion-container"><p style="color:#0891B2; font-weight:bold;">💡 EXPLICACIÓN</p>{exp}</div>', unsafe_allow_html=True)
    
    # Navegación horizontal (Replica tu diseño favorito)
    nav = st.container(horizontal=True)
    with nav:
        if idx > 0 and st.button("⬅️ ANTERIOR", key="rev_p", use_container_width=True):
            st.session_state.indice_revision -= 1
            st.rerun()
        
        txt_volver = "VOLVER AL HISTORIAL" if st.session_state.get("sub_pantalla") == "repaso_historial" else "VOLVER AL RESUMEN"
        if st.button(txt_volver, use_container_width=True):
            st.session_state.ver_revision = False
            if st.session_state.get("sub_pantalla") == "repaso_historial":
                st.session_state.sub_pantalla = "historial"
            st.rerun()

        if idx < len(lista_preguntas) - 1 and st.button("SIGUIENTE ➡️", key="rev_n", use_container_width=True):
            st.session_state.indice_revision += 1
            st.rerun()

def _render_resultado_final(lista_preguntas, limpiar_estado_maestro):
    # Lógica de cálculo (Extraída de tu código original)
    total = len(lista_preguntas)
    resps = st.session_state.respuestas_usuario
    aciertos = sum(1 for i, p in enumerate(lista_preguntas) if resps.get(i) == p["correcta"])
    fallos = sum(1 for i, p in enumerate(lista_preguntas) if resps.get(i) and resps.get(i) != p["correcta"])
    resumen = Examen(total=total, aciertos=aciertos, fallos=fallos)
    
    color = "#2ecc71" if resumen.nota_sobre_diez >= 5 else "#e74c3c"
    
    st.markdown(f'<h2 style="text-align:center; color:{color};">{"¡ENHORABUENA!" if resumen.nota_sobre_diez >= 5 else "SIGUE INTENTÁNDOLO"}</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="tarjeta-nota-final" style="background:{color};"><p>PUNTUACIÓN FINAL</p><h1>{resumen.nota_sobre_diez:.2f}</h1><p>sobre 10</p></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="stat-box" style="border-color:#2ecc71; background:rgba(46,204,113,0.1); color:#2ecc71;">✅ ACIERTOS<br><b>{aciertos}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="border-color:#bdc3c7; background:rgba(189,195,199,0.1); color:#bdc3c7;">⚪ BLANCOS<br><b>{resumen.blancos}</b></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box" style="border-color:#e74c3c; background:rgba(231,76,60,0.1); color:#e74c3c;">❌ FALLOS<br><b>{fallos}</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-box" style="border-color:#6D28D9; background:rgba(109,40,217,0.1); color:#6D28D9;">🎯 NETAS<br><b>{resumen.netas:.2f}</b></div>', unsafe_allow_html=True)

    if st.button("🔍 REVISAR PREGUNTAS", use_container_width=True):
        st.session_state.ver_revision = True
        st.session_state.indice_revision = 0
        st.rerun()
    if st.button("🏁 SALIR AL MENÚ", use_container_width=True, type="primary"):
        limpiar_estado_maestro()
        st.session_state.sub_pantalla = "seleccion_tema"
        st.rerun()

def _render_pregunta_activa(lista_preguntas):
    idx = st.session_state.indice_pregunta
    p = lista_preguntas[idx]
    
    st.progress((idx + 1) / len(lista_preguntas), text=f"Pregunta {idx + 1} de {len(lista_preguntas)}")
    st.markdown(f"#### {p['enunciado']}")

    res_actual = st.session_state.respuestas_usuario.get(idx)
    letras = ["A", "B", "C"]
    
    seleccion = st.radio(
        "Selecciona respuesta:", letras,
        format_func=lambda x: f"{x}) {p[f'opcion_{x.lower()}']}",
        index=letras.index(res_actual) if res_actual in letras else None,
        key=f"r_{idx}"
    )
    if seleccion: st.session_state.respuestas_usuario[idx] = seleccion

    st.write("---")
    nav = st.container(horizontal=True)
    with nav:
        # Botón Anterior
        btn_ant = st.button("⬅️ Anterior", use_container_width=True, disabled=(idx == 0))
        if btn_ant:
            st.session_state.indice_pregunta -= 1
            st.rerun()

        # Botón Siguiente / Finalizar
        es_ultima = (idx == len(lista_preguntas) - 1)
        txt_sig = "🏁 Finalizar" if es_ultima else "Siguiente ➡️"
        if st.button(txt_sig, use_container_width=True, type="primary"):
            if es_ultima:
                # Aquí llamarías a tu lógica de guardado
                st.session_state.examen_finalizado = True
            else:
                st.session_state.indice_pregunta += 1
            st.rerun()