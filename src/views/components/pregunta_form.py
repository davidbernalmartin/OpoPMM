"""Reusable question form component."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st


def renderizar_formulario_edicion_pregunta(p: dict[str, Any], nombres_temas: list[str]) -> tuple:
    """Render admin question edit form and return collected values."""
    for key in list(p.keys()):
        if pd.isna(p[key]):
            p[key] = ""

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<p class="label-admin">ENUNCIADO DE LA PREGUNTA:</p>', unsafe_allow_html=True)
            f_enun = st.text_area(
                "##enun",
                value=str(p["enunciado"]),
                height=150,
                label_visibility="collapsed",
                key=f"enun_{p['id']}",
            )
        with col2:
            st.markdown('<p class="label-admin">EXPLICACIÓN / BASE LEGAL:</p>', unsafe_allow_html=True)
            f_exp = st.text_area(
                "##exp",
                value=str(p.get("explicacion", "")),
                height=150,
                label_visibility="collapsed",
                key=f"exp_{p['id']}",
            )

        st.write("###")
        col_izq, col_der = st.columns(2)

        with col_izq:
            st.markdown('<p class="label-admin">OPCIONES DE RESPUESTA:</p>', unsafe_allow_html=True)
            opciones_vals = {}
            for letra in ["a", "b", "c"]:
                c_lab, c_inp = st.columns([0.05, 0.95])
                c_lab.markdown(f'<p style="margin-top:10px; font-weight:bold;">{letra.upper()}:</p>', unsafe_allow_html=True)
                opciones_vals[letra] = c_inp.text_input(
                    f"L_{letra}",
                    value=str(p[f"opcion_{letra}"]),
                    label_visibility="collapsed",
                    key=f"in_{letra}_{p['id']}",
                )
            f_a, f_b, f_c = opciones_vals["a"], opciones_vals["b"], opciones_vals["c"]

        with col_der:
            st.markdown('<p class="label-admin">CONFIGURACIÓN:</p>', unsafe_allow_html=True)
            c_lab_corr, c_inp_corr = st.columns([0.2, 0.8])
            c_lab_corr.markdown('<p style="margin-top:10px; font-weight:bold;">Correcta:</p>', unsafe_allow_html=True)

            val_correcta_db = str(p.get("correcta", "A")).upper().strip()
            opciones = ["A", "B", "C"]
            idx_corr = opciones.index(val_correcta_db) if val_correcta_db in opciones else 0
            f_corr = c_inp_corr.selectbox(
                "Corr", opciones, index=idx_corr, label_visibility="collapsed", key=f"corr_{p['id']}"
            )

            c_lab_tema, c_inp_tema = st.columns([0.2, 0.8])
            c_lab_tema.markdown('<p style="margin-top:10px; font-weight:bold;">Tema:</p>', unsafe_allow_html=True)
            tema_actual = p.get("tema_nombre", "")
            idx_tema = nombres_temas.index(tema_actual) if tema_actual in nombres_temas else 0
            f_tema_sel = c_inp_tema.selectbox(
                "TemaSel", nombres_temas, index=idx_tema, label_visibility="collapsed", key=f"tema_{p['id']}"
            )

    return f_enun, f_exp, f_a, f_b, f_c, f_corr, f_tema_sel
