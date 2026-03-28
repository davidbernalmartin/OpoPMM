"""Runtime exam rendering helpers."""

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
    if st.session_state.get("ver_revision", False):
        idx_rev = st.session_state.get("indice_revision", 0)
        p = lista_preguntas[idx_rev]
        resp_usuario = st.session_state.respuestas_usuario.get(idx_rev)
        es_correcta = resp_usuario == p["correcta"]

        st.progress((idx_rev + 1) / len(lista_preguntas), text=f"Revisando Pregunta {idx_rev + 1} de {len(lista_preguntas)}")
        st.markdown(f"#### {p['enunciado']}")

        opciones = [("A", p["opcion_a"]), ("B", p["opcion_b"]), ("C", p["opcion_c"])]
        for letra, texto in opciones:
            base_style = "padding: 12px; border-radius: 10px; margin: 8px 0; border-left: 5px solid "
            if letra == p["correcta"]:
                st.markdown(
                    f"""<div style=" {base_style} #2ecc71; background-color: rgba(46, 204, 113, 0.15);"><b style="color: white;">{letra}) {texto}</b> 
                        <span style="color: #2ecc71; margin-left: 10px;">(Correcta)</span>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
            elif letra == resp_usuario and not es_correcta:
                st.markdown(
                    f"""
                    <div style=" {base_style} #e74c3c; background-color: rgba(231, 76, 60, 0.15);">
                        <span style="color: white;">{letra}) {texto}</span> <span style="color: #e74c3c; margin-left: 10px;">(Tu elección)</span>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style=" {base_style} transparent; background-color: transparent;">
                        <span style="color: #bdc3c7;">{letra}) {texto}</span>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

        st.write("---")
        exp_raw = p.get("explicacion", "")
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
            st.caption("No hay explicación disponible para esta pregunta.")
        st.write("---")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if idx_rev > 0 and st.button("⬅️ ANTERIOR", key="rev_prev", width='stretch'):
                st.session_state.indice_revision -= 1
                st.rerun()
        with c2:
            # Detectamos si es un repaso del historial o un examen recién hecho
            es_repaso = st.session_state.get("sub_pantalla") == "repaso_historial"
            texto_boton = "VOLVER AL HISTORIAL" if es_repaso else "VOLVER AL RESUMEN"
            
            if st.button(texto_boton, width='stretch'):
                if es_repaso:
                    st.session_state.ver_revision = False
                    st.session_state.sub_pantalla = "historial" # Volvemos a la lista
                else:
                    st.session_state.ver_revision = False # Volvemos al resumen de notas
                st.rerun()
        with c3:
            if idx_rev < len(lista_preguntas) - 1 and st.button("SIGUIENTE ➡️", key="rev_next", width='stretch'):
                st.session_state.indice_revision += 1
                st.rerun()

    elif st.session_state.examen_finalizado:
        # 1. Cálculos iniciales
        total = len(lista_preguntas)
        respuestas = st.session_state.respuestas_usuario
        aciertos = sum(1 for i, p in enumerate(lista_preguntas) if respuestas.get(i) == p["correcta"])
        fallos = sum(1 for i, p in enumerate(lista_preguntas) if respuestas.get(i) is not None and respuestas.get(i) != p["correcta"])
        resumen = Examen(total=total, aciertos=aciertos, fallos=fallos)
        sin_responder = resumen.blancos
        netas = resumen.netas
        nota_diez = resumen.nota_sobre_diez
        # 2. Lógica de colores dinámicos (Arquitectura Visual)
        color_resultado = "#2ecc71" if nota_diez >= 5 else "#e74c3c"
        mensaje_resultado = "¡ENHORABUENA!" if nota_diez >= 5 else "SIGUE INTENTÁNDOLO"
        # 3. Renderizado Optimizado para Móvil
        st.markdown(f'<h2 style="text-align: center; color: {color_resultado};">{mensaje_resultado}</h2>', unsafe_allow_html=True)
        # Tarjeta de Nota Principal (Ancho completo para impacto visual)
        st.markdown(
            f"""<div style="background-color: {color_resultado}; padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                <p style="margin:0; font-size: 1.2rem; color: white; opacity: 0.9; font-weight: bold;">PUNTUACIÓN FINAL</p>
                <h1 style="margin:0; color: white; font-size: 4.5rem; line-height: 1;">{nota_diez:.2f}</h1>
                <p style="margin:0; font-size: 1rem; color: white;">sobre 10 puntos</p>
            </div>""",
            unsafe_allow_html=True,
        )
        # Estadísticas en Grid 2x2 (Mejor que 3 columnas en móvil)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div style="background-color: rgba(46, 204, 113, 0.1); border: 1px solid #2ecc71; padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 10px;">
                <span style="font-size: 0.9rem; color: #2ecc71;">✅ ACIERTOS</span><br><b style="font-size: 1.5rem;">{aciertos}</b>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div style="background-color: rgba(189, 195, 199, 0.1); border: 1px solid #bdc3c7; padding: 15px; border-radius: 15px; text-align: center;">
                <span style="font-size: 0.9rem; color: #bdc3c7;">⚪ BLANCOS</span><br><b style="font-size: 1.5rem;">{sin_responder}</b>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div style="background-color: rgba(231, 76, 60, 0.1); border: 1px solid #e74c3c; padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 10px;">
                <span style="font-size: 0.9rem; color: #e74c3c;">❌ FALLOS</span><br><b style="font-size: 1.5rem;">{fallos}</b>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div style="background-color: rgba(109, 40, 217, 0.1); border: 1px solid #6D28D9; padding: 15px; border-radius: 15px; text-align: center;">
                <span style="font-size: 0.9rem; color: #6D28D9;">🎯 NETAS</span><br><b style="font-size: 1.5rem;">{netas:.2f}</b>
            </div>""", unsafe_allow_html=True)
        st.write("###")
        # Botones de acción vertical para móvil (Fáciles de pulsar)
        if st.button("🔍 REVISAR PREGUNTAS", width='stretch', type="secondary"):
            st.session_state.ver_revision = True
            st.session_state.indice_revision = 0
            st.rerun()
        if st.button("🏁 SALIR AL MENÚ", width='stretch', type="primary"):
            st.session_state.ver_revision = False
            limpiar_estado_maestro()
            st.session_state.sub_pantalla = "seleccion_tema"
            st.rerun()
    else:
        idx = st.session_state.indice_pregunta
        p_actual = lista_preguntas[idx]

        st.progress((idx + 1) / len(lista_preguntas), text=f"Pregunta {idx + 1} de {len(lista_preguntas)}")
        st.markdown(f"#### {p_actual['enunciado']}")

        opciones_letras = ["A", "B", "C"]
        respuesta_guardada = st.session_state.respuestas_usuario.get(idx)
        indice_a_mostrar = opciones_letras.index(respuesta_guardada) if respuesta_guardada in opciones_letras else None
        opciones_texto = {"A": p_actual["opcion_a"], "B": p_actual["opcion_b"], "C": p_actual["opcion_c"]}

        seleccion = st.radio(
            "Selecciona tu respuesta:",
            options=opciones_letras,
            format_func=lambda x: f"{x}) {opciones_texto[x]}",
            index=indice_a_mostrar,
            key=f"radio_preg_{idx}",
        )

        if seleccion:
            st.session_state.respuestas_usuario[idx] = seleccion

        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if idx > 0 and st.button("⬅️ ANTERIOR", width='stretch'):
                st.session_state.indice_pregunta -= 1
                st.rerun()
        with col2:
            if idx < len(lista_preguntas) - 1:
                if st.button("SIGUIENTE ➡️", width='stretch'):
                    st.session_state.indice_pregunta += 1
                    st.rerun()
            elif st.button("🏁 FINALIZAR Y GUARDAR", width='stretch'):
                guardar_resultado_examen(
                    st.session_state.preguntas_examen,
                    st.session_state.respuestas_usuario,
                    tipo=st.session_state.get("tipo_test_actual", "Personalizado"),
                )
                st.session_state.examen_finalizado = True
                st.rerun()
