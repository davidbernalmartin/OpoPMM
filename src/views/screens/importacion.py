"""Import dialogs for CSV and PDF question ingestion."""

from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st

from src.services.import_service import parsear_examen_universal


def get_modal_importar_pdf() -> Callable[[], None]:
    @st.dialog("Importar desde PDF")
    def modal_importar_pdf() -> None:
        st.write("Sube el archivo PDF del examen. El sistema intentará extraer las preguntas y opciones automáticamente.")
        archivo = st.file_uploader("Seleccionar PDF", type=["pdf"], key="uploader_pdf_modal")

        if archivo:
            with st.spinner("Analizando estructura del examen..."):
                try:
                    lista_preguntas = parsear_examen_universal(archivo)
                    if lista_preguntas:
                        st.session_state.preguntas_pendientes = lista_preguntas
                        st.session_state.sub_pantalla = "revision_importacion"
                        st.rerun()
                    else:
                        st.error("No se detectaron preguntas. Asegúrate de que el PDF tenga el formato 1. Enunciado A. B. C.")
                except Exception as e:
                    st.error(f"Error al procesar el PDF: {e}")

    return modal_importar_pdf


def get_modal_importar_csv() -> Callable[[], None]:
    @st.dialog("Subir archivo de preguntas")
    def modal_importar_csv() -> None:
        st.write("Selecciona un archivo CSV con el formato correcto.")
        archivo = st.file_uploader("Arrastra tu archivo aquí", type=["csv"], key="uploader_modal")

        if archivo:
            try:
                df_temp = pd.read_csv(
                    archivo,
                    sep=";",
                    encoding="utf-8",
                    header=0,
                    names=["enunciado", "opcion_a", "opcion_b", "opcion_c", "correcta", "explicacion", "tema_id"],
                ).fillna("")

                st.session_state.preguntas_pendientes = df_temp.to_dict("records")
                st.session_state.sub_pantalla = "revision_importacion"
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    return modal_importar_csv
