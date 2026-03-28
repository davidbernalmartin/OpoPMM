"""Admin question management screens."""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd
import streamlit as st


def render_admin_preguntas_screens(
    *,
    supabase: Any,
    renderizar_formulario_edicion: Callable[[dict[str, Any], list[str]], tuple],
    modal_importar_pdf: Callable[[], None],
    modal_importar: Callable[[], None],
    limpiar_estado_maestro: Callable[[], None],
    convertir_a_csv: Callable[[list[dict]], bytes],
) -> None:
    """
    Render admin question screens. 
    Eliminada la validación de sub_pantalla para compatibilidad con Tabs.
    """
    # Si estamos en proceso de revisión de una importación, mostramos esa pantalla
    if st.session_state.get("sub_pantalla") == "revision_importacion":
        _render_revision_importacion(
            supabase=supabase,
            limpiar_estado_maestro=limpiar_estado_maestro,
            convertir_a_csv=convertir_a_csv,
        )
    # En cualquier otro caso (cuando entramos al Tab), mostramos el panel principal
    else:
        _render_admin_preguntas(
            supabase=supabase,
            renderizar_formulario_edicion=renderizar_formulario_edicion,
            modal_importar_pdf=modal_importar_pdf,
            modal_importar=modal_importar,
        )


def _render_admin_preguntas(
    *,
    supabase: Any,
    renderizar_formulario_edicion: Callable[[dict[str, Any], list[str]], tuple],
    modal_importar_pdf: Callable[[], None],
    modal_importar: Callable[[], None],
) -> None:
    st.markdown('<div class="titulo-pantalla">PANEL DE GESTIÓN DE PREGUNTAS</div>', unsafe_allow_html=True)

    res_temas = supabase.table("temas").select("id, nombre").execute()
    id_a_nombre = {t["id"]: t["nombre"] for t in res_temas.data}
    nombre_a_id = {t["nombre"]: t["id"] for t in res_temas.data}
    nombres_temas = sorted(list(nombre_a_id.keys()))

    if st.session_state.get("modo_creacion_pregunta", False):
        st.markdown(
            """
            <style>
                input, textarea, div[data-baseweb="select"] {
                    border: 2px solid #00F2FE !important;
                    box-shadow: 0 0 12px rgba(0, 242, 254, 0.6) !important;
                }
                @keyframes pulse-border {
                    0% { box-shadow: 0 0 5px rgba(0, 242, 254, 0.4); }
                    50% { box-shadow: 0 0 15px rgba(0, 242, 254, 0.8); }
                    100% { box-shadow: 0 0 5px rgba(0, 242, 254, 0.4); }
                }
                input, textarea { animation: pulse-border 2s infinite !important; }
            </style>
        """,
            unsafe_allow_html=True,
        )

    res_p = supabase.table("preguntas").select("*").order("id", desc=True).execute()
    if res_p.data:
        df_p = pd.DataFrame(res_p.data)
        df_p["tema_nombre"] = df_p["tema_id"].map(id_a_nombre).fillna("Sin Tema")

        st.write("### 📋 Banco de Preguntas")
        event = st.dataframe(
            df_p,
            column_order=("id", "enunciado", "tema_nombre"),
            column_config={
                "id": st.column_config.Column("ID", width=50),
                "enunciado": st.column_config.TextColumn("Enunciado", width=800),
                "tema_nombre": st.column_config.TextColumn("Tema", width="medium"),
            },
            hide_index=True,
            width='stretch',
            on_select="rerun",
            selection_mode="single-row",
            key="tabla_admin_preguntas",
        )

        if event.selection.rows:
            st.session_state.modo_creacion_pregunta = False
            st.session_state.p_seleccionada = df_p.iloc[event.selection.rows[0]].to_dict()

    st.divider()
    modo_crear = st.session_state.get("modo_creacion_pregunta", False)
    p_sel = st.session_state.get("p_seleccionada")

    if modo_crear:
        st.markdown('<h3 style="color: #00F2FE;">➕ CREANDO NUEVA PREGUNTA</h3>', unsafe_allow_html=True)
        p_init = {
            "id": None,
            "enunciado": "",
            "explicacion": "",
            "opcion_a": "",
            "opcion_b": "",
            "opcion_c": "",
            "correcta": "A",
            "tema_id": res_temas.data[0]["id"] if res_temas.data else None,
        }
        f_vals = renderizar_formulario_edicion(p_init, nombres_temas)
    elif p_sel:
        st.markdown('<h3 style="color: #FFA500;">📝 EDITANDO PREGUNTA</h3>', unsafe_allow_html=True)
        f_vals = renderizar_formulario_edicion(p_sel, nombres_temas)
    else:
        st.info("💡 Selecciona una pregunta o pulsa 'NUEVA'.")
        f_vals = None

    st.write("###")
    b1, b2, b3, b4, b5 = st.columns(5)

    with b1:
        if st.button("➕ NUEVA", width='stretch', key="btn_nueva"):
            st.session_state.p_seleccionada = None
            st.session_state.modo_creacion_pregunta = True
            st.rerun()

    with b2:
        if st.button("📄 PDF A REVISIÓN", width='stretch', key="btn_pdf"):
            modal_importar_pdf()

    with b3:
        if st.button("📤 IMPORTAR", width='stretch', key="btn_import_trigger"):
            modal_importar()

    with b4:
        if f_vals and st.button("💾 GUARDAR", type="primary", width='stretch'):
            try:
                nombre_tema_sel = f_vals[6]
                id_tema_final = nombre_a_id.get(nombre_tema_sel)

                if not id_tema_final:
                    st.error("❌ Tema no válido")
                else:
                    upd = {
                        "enunciado": str(f_vals[0]).strip(),
                        "explicacion": str(f_vals[1]).strip(),
                        "opcion_a": str(f_vals[2]).strip(),
                        "opcion_b": str(f_vals[3]).strip(),
                        "opcion_c": str(f_vals[4]).strip(),
                        "correcta": str(f_vals[5]).upper().strip(),
                        "tema_id": id_tema_final,
                    }

                    with st.spinner("Guardando..."):
                        if modo_crear:
                            supabase.table("preguntas").insert(upd).execute()
                            st.success("✅ Creada")
                        else:
                            supabase.table("preguntas").update(upd).eq("id", p_sel["id"]).execute()
                            st.success("✅ Actualizada")

                        st.session_state.modo_creacion_pregunta = False
                        st.session_state.p_seleccionada = None
                        st.rerun()
            except Exception as e:
                st.error(f"Error técnico: {str(e)}")

    with b5:
        if p_sel and not modo_crear:
            if st.button("🗑️ ELIMINAR", width='stretch'):
                supabase.table("preguntas").delete().eq("id", p_sel["id"]).execute()
                st.session_state.p_seleccionada = None
                st.rerun()
        else:
            st.button("🗑️ ELIMINAR", width='stretch', disabled=True)


def _render_revision_importacion(
    *, supabase: Any, limpiar_estado_maestro: Callable[[], None], convertir_a_csv: Callable[[list[dict]], bytes]
) -> None:
    st.markdown('<div class="titulo-pantalla">🧐 REVISIÓN DE PREGUNTAS IMPORTADAS</div>', unsafe_allow_html=True)

    if not st.session_state.get("preguntas_pendientes"):
        st.warning("No quedan preguntas para revisar.")
        if st.button("⬅️ VOLVER AL PANEL"):
            limpiar_estado_maestro()
            st.session_state.sub_pantalla = "admin_preguntas"
            st.rerun()
        st.stop()

    res_t = supabase.table("temas").select("id, nombre").execute()
    nombres_temas = sorted([t["nombre"] for t in res_t.data])
    nom_a_id = {t["nombre"]: t["id"] for t in res_t.data}
    id_a_nom = {t["id"]: t["nombre"] for t in res_t.data}

    st.info(f"Tienes **{len(st.session_state.preguntas_pendientes)}** preguntas pendientes de importar.")

    preguntas_para_subir = []

    for i, p in enumerate(st.session_state.preguntas_pendientes):
        with st.expander(f"Pregunta {i+1}: {str(p.get('Enunciado'))[:80]}...", expanded=(i == 0)):
            col_izq, col_der = st.columns([2, 1])

            with col_izq:
                enun = st.text_area("Enunciado", value=p.get("Enunciado"), key=f"rev_enun_{i}", height=120)
                exp = st.text_area(
                    "Explicación / Base Legal", value=p.get("Explicación"), key=f"rev_exp_{i}", height=100
                )

            with col_der:
                if st.button(f"🗑️ ELIMINAR PREGUNTA {i+1}", key=f"btn_del_{i}", width='stretch'):
                    st.session_state.preguntas_pendientes.pop(i)
                    st.rerun()

                tema_id_csv = p.get("Tema")
                try:
                    tema_id_val = int(tema_id_csv)
                    nombre_preasignado = id_a_nom.get(tema_id_val)
                except Exception:
                    nombre_preasignado = None
                idx_t = nombres_temas.index(nombre_preasignado) if nombre_preasignado in nombres_temas else 0
                t_sel = st.selectbox("Asignar Tema", nombres_temas, index=idx_t, key=f"rev_tema_{i}")

                corr_csv = str(p.get("correcta", "A")).strip().upper()
                idx_c = ["A", "B", "C"].index(corr_csv) if corr_csv in ["A", "B", "C"] else 0
                c_sel = st.selectbox("Opción Correcta", ["A", "B", "C"], index=idx_c, key=f"rev_corr_{i}")

            st.divider()
            st.write("**Opciones de respuesta:**")

            opciones_editadas = {}
            for letra, campo in zip(["A", "B", "C"], ["opcion_a", "opcion_b", "opcion_c"]):
                c_label, c_input = st.columns([0.1, 2.9])
                with c_label:
                    st.markdown(f"<p style=margin-top:10px; font-weight:bold;'>{letra}</p>", unsafe_allow_html=True)
                with c_input:
                    opciones_editadas[letra] = st.text_input(
                        f"Contenido de la opción {letra}",
                        value=p.get(campo),
                        key=f"rev_{letra.lower()}_{i}",
                        label_visibility="collapsed",
                    )

            preguntas_para_subir.append(
                {
                    "enunciado": enun,
                    "opcion_a": opciones_editadas["A"],
                    "opcion_b": opciones_editadas["B"],
                    "opcion_c": opciones_editadas["C"],
                    "correcta": c_sel.upper(),
                    "explicacion": exp,
                    "tema_id": nom_a_id[t_sel],
                }
            )

    st.divider()
    c_bot1, c_bot2, c_bot3 = st.columns(3)

    with c_bot1:
        if st.button("❌ CANCELAR TODO", width='stretch'):
            st.session_state.preguntas_pendientes = []
            limpiar_estado_maestro()
            st.session_state.sub_pantalla = "admin_preguntas"
            st.rerun()

    with c_bot2:
        csv_data = convertir_a_csv(preguntas_para_subir)
        st.download_button(
            label="💾 GUARDAR PROGRESO (CSV)",
            data=csv_data,
            file_name="revision_parcial_examen.csv",
            mime="text/csv",
            width='stretch',
            help="Descarga lo que llevas hecho para seguir en otro momento",
        )

    with c_bot3:
        if st.button("🚀 SUBIR A BASE DE DATOS", type="primary", width='stretch'):
            if preguntas_para_subir:
                with st.spinner("Guardando en Supabase..."):
                    supabase.table("preguntas").insert(preguntas_para_subir).execute()
                    st.success(f"¡{len(preguntas_para_subir)} preguntas añadidas!")
                    st.session_state.preguntas_pendientes = []
                    limpiar_estado_maestro()
                    st.session_state.sub_pantalla = "admin_preguntas"
                    st.rerun()

            st.session_state.paso_configuracion = "principal"
            st.rerun()
