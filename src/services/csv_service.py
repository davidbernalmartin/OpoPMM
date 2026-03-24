"""CSV helpers for question import/export."""

from __future__ import annotations

import pandas as pd


def convertir_preguntas_a_csv(lista_preguntas: list[dict]) -> bytes:
    df_descarga = pd.DataFrame(lista_preguntas)
    df_descarga = df_descarga.rename(
        columns={
            "enunciado": "Enunciado",
            "opcion_a": "opcion_a",
            "opcion_b": "opcion_b",
            "opcion_c": "opcion_c",
            "correcta": "correcta",
            "explicacion": "Explicación",
        }
    )
    return df_descarga.to_csv(index=False, sep=";").encode("utf-8")
