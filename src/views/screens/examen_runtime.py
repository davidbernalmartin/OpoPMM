from __future__ import annotations

import time
from typing import Any, Callable

import streamlit as st

from src.models.examen import Examen
from src.views.components.pregunta_form import renderizar_formulario_edicion_pregunta


@st.dialog("📢 Reportar Error o Duda")
def modal_enviar_feedback(pregunta, supabase):
    st.markdown(f"**Pregunta ID:** `{pregunta['id']}`")
    st.info("Escribe tu duda o reporta un error. Te responderemos en tu perfil.")

    comentario = st.text_area("Tu mensaje:", placeholder="Ej: La respuesta correcta creo que es la B porque...", height=150)

    col1, col2 = st.columns(2)
    if col1.button("ENVIAR REPORTE", type="primary", use_container_width=True):
        if not comentario.strip():
            st.error("Escribe algo antes de enviar.")
            return
        try:
            supabase.table("feedback_tickets").insert({
                "user_id": st.session_state.user.id,
                "pregunta_id": pregunta["id"],
                "mensaje_usuario": comentario,
                "enunciado_momento": pregunta["enunciado"],
            }).execute()
            st.success("✅ Enviado. Podrás ver la respuesta en tu Perfil.")
            time.sleep(1.5)
            st.rerun()
        except Exception as e:
            st.error(f"Error al enviar: {e}")

    if col2.button("CANCELAR", use_container_width=True):
        st.rerun()


@st.dialog("✏️ Editor de Pregunta", width="large")
def modal_editar_pregunta(pregunta, supabase):
    res_temas = supabase.table("temas").select("id, nombre").execute()
    temas_db = res_temas.data if res_temas.data else []
    temas_nombres = [t["nombre"] for t in temas_db]
    temas_dict = {t["nombre"]: t["id"] for t in temas_db}
    id_a_nombre = {t["id"]: t["nombre"] for t in temas_db}

    pregunta["tema_nombre"] = id_a_nombre.get(pregunta.get("tema_id"), "")
    st.subheader("Edición de Pregunta" if pregunta.get("id") else "Nueva Pregunta")

    f_enun, f_exp, f_a, f_b, f_c, f_corr, f_tema_nom = renderizar_formulario_edicion_pregunta(pregunta, temas_nombres)

    st.divider()
    col_g, col_c = st.columns(2)

    if col_g.button("💾 GUARDAR CAMBIOS", type="primary", width="stretch"):
        data_save = {
            "enunciado": f_enun,
            "explicacion": f_exp,
            "opcion_a": f_a,
            "opcion_b": f_b,
            "opcion_c": f_c,
            "correcta": f_corr,
            "tema_id": temas_dict.get(f_tema_nom),
        }
        with st.spinner("Sincronizando con base de datos..."):
            try:
                supabase.table("preguntas").update(data_save).eq("id", pregunta["id"]).execute()
                pregunta.update(data_save)
                pregunta["tema_nombre"] = f_tema_nom
                st.success("✅ ¡Base de datos y vista sincronizadas!")
                time.sleep(0.8)
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    if col_c.button("❌ CANCELAR", width="stretch"):
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

    if st.session_state.get("ver_revision", False):
        _render_revision(lista_preguntas, supabase)
    elif st.session_state.examen_finalizado:
        _render_resultado_final(lista_preguntas, limpiar_estado_maestro)
    else:
        _render_pregunta_activa(lista_preguntas, guardar_resultado_examen, titulo)


def _render_revision(lista_preguntas, supabase):
    idx = st.session_state.get("indice_revision", 0)
    p = lista_preguntas[idx]
    resp_u = st.session_state.respuestas_usuario.get(idx)
    dudosas = st.session_state.get("preguntas_dudosas", {})
    es_dudosa = dudosas.get(idx, False) or dudosas.get(str(idx), False)
    correcta = p.get("correcta", "A").upper()

    st.progress((idx + 1) / len(lista_preguntas), text=f"Revisando {idx + 1} de {len(lista_preguntas)}")

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
        if letra == p["correcta"]:
            st.markdown(f'<div class="opcion-revision" style="border-left-color: #2ecc71; background: rgba(46,204,113,0.15); font-weight: bold;">{letra}) {texto} <span style="color:#2ecc71;">(Correcta)</span></div>', unsafe_allow_html=True)
        elif letra == resp_u:
            st.markdown(f'<div class="opcion-revision" style="border-left-color: #e74c3c; background: rgba(231,76,60,0.15);">{letra}) {texto} <span style="color:#e74c3c;">(Tu elección)</span></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="opcion-revision" style="color: #bdc3c7;">{letra}) {texto}</div>', unsafe_allow_html=True)

    st.write("---")
    exp = p.get("explicacion", "")
    if exp and str(exp).strip():
        st.markdown(f'<div class="explicacion-container"><p style="color:#0891B2; font-weight:bold;">💡 EXPLICACIÓN</p>{exp}</div>', unsafe_allow_html=True)
        st.write("---")

    nav = st.container(horizontal=True)
    with nav:
        if idx > 0 and st.button("⬅️ ANTERIOR", key="rev_p", width="stretch"):
            st.session_state.indice_revision -= 1
            st.rerun()

        txt_volver = "VOLVER AL HISTORIAL" if st.session_state.get("sub_pantalla") == "repaso_historial" else "VOLVER AL RESUMEN"
        if st.button(txt_volver, width="stretch"):
            st.session_state.ver_revision = False
            if st.session_state.get("sub_pantalla") == "repaso_historial":
                st.session_state.sub_pantalla = "historial"
            st.rerun()

        if idx < len(lista_preguntas) - 1 and st.button("SIGUIENTE ➡️", key="rev_n", width="stretch"):
            st.session_state.indice_revision += 1
            st.rerun()

        if st.session_state.get("user_role") == "admin":
            if st.button("🛠️ Modificar esta pregunta", use_container_width=True):
                modal_editar_pregunta(p, supabase)
        else:
            if st.button("🛠️ Reportar error o duda", use_container_width=True):
                modal_enviar_feedback(p, supabase)


def _render_resultado_final(lista_preguntas, limpiar_estado_maestro):
    total = len(lista_preguntas)
    resps = st.session_state.respuestas_usuario
    dudas = st.session_state.get("preguntas_dudosas", {})

    aciertos_r = sum(1 for i, p in enumerate(lista_preguntas) if resps.get(i) == p["correcta"])
    fallos_r = sum(1 for i, p in enumerate(lista_preguntas) if resps.get(i) and resps.get(i) != p["correcta"])
    res_real = Examen(total=total, aciertos=aciertos_r, fallos=fallos_r)

    aciertos_c = sum(1 for i, p in enumerate(lista_preguntas) if resps.get(i) == p["correcta"] and not dudas.get(i))
    fallos_c = sum(1 for i, p in enumerate(lista_preguntas) if resps.get(i) and resps.get(i) != p["correcta"] and not dudas.get(i))
    res_cons = Examen(total=total, aciertos=aciertos_c, fallos=fallos_c)

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
        if st.button("🔍 REVISAR PREGUNTAS", width="stretch"):
            st.session_state.ver_revision = True
            st.session_state.indice_revision = 0
            st.rerun()
        if st.button("🏁 SALIR AL MENÚ", width="stretch", type="primary"):
            limpiar_estado_maestro()
            st.session_state.sub_pantalla = "seleccion_tema"
            st.rerun()


def _render_pregunta_activa(lista_preguntas, guardar_resultado_examen, titulo):
    idx = st.session_state.indice_pregunta
    p = lista_preguntas[idx]

    st.progress((idx + 1) / len(lista_preguntas), text=f"Pregunta {idx + 1} de {len(lista_preguntas)}")
    st.markdown(f'<div class="enunciado-container">{p["enunciado"]}</div>', unsafe_allow_html=True)

    res_actual = st.session_state.respuestas_usuario.get(idx)
    letras = ["A", "B", "C"]

    seleccion = st.radio(
        "Selecciona respuesta:", letras,
        format_func=lambda x: f"{x}) {p[f'opcion_{x.lower()}']}",
        index=letras.index(res_actual) if res_actual in letras else None,
        key=f"r_{idx}",
    )
    if seleccion:
        st.session_state.respuestas_usuario[idx] = seleccion

    if "preguntas_dudosas" not in st.session_state:
        st.session_state.preguntas_dudosas = {}

    es_dudosa = st.toggle(
        "❔ Dudosa",
        value=st.session_state.preguntas_dudosas.get(idx, False),
        key=f"duda_{idx}",
        help="Marca esta casilla si no estás seguro. Calcularemos tu nota simulando que la dejas en blanco.",
    )
    st.session_state.preguntas_dudosas[idx] = es_dudosa

    if es_dudosa:
        st.warning("💡 Pregunta marcada para el análisis de riesgo.")

    st.write("---")
    nav = st.container(horizontal=True)
    with nav:
        btn_ant = st.button("⬅️ Anterior", width="stretch", disabled=(idx == 0))
        if btn_ant:
            st.session_state.indice_pregunta -= 1
            st.rerun()

        es_ultima = idx == len(lista_preguntas) - 1
        txt_sig = "🏁 Finalizar" if es_ultima else "Siguiente ➡️"
        if st.button(txt_sig, width="stretch", type="primary"):
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
