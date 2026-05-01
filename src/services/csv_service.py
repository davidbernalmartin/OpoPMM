"""CSV helpers for question import/export."""

from __future__ import annotations

import pandas as pd


def convertir_preguntas_a_csv(lista_preguntas: list[dict]) -> bytes:
    df = pd.DataFrame(lista_preguntas).rename(columns={
        "enunciado": "Enunciado",
        "explicacion": "Explicación",
    })
    return df.to_csv(index=False, sep=";").encode("utf-8")
