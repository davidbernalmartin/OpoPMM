"""Services for parsing imported exam files."""

from __future__ import annotations

import re
from typing import Any

import pdfplumber


def limpiar_ruido_general(texto: str) -> str:
    """Limpia cabeceras, pies y avisos de continuidad de páginas."""
    patrones = [
        r"(?i)POLIC[ÍI]A\s+MUNICIPAL\s+MADRID",
        r"(?i)AYUNTAMIENTO\s+DE\s+MADRID",
        r"(?i)CUESTIONARIO\s+[A-Z]",
        r"(?i)P[ÁA]GINA\s+\d+",
        r"(?i)POL-B\s*-\s*\d+",
        r"(?i)Continúe\s+en\s+la\s+siguiente\s+página",
        r"(?i)Ha\s+finalizado\s+la\s+prueba",
        r"---\s+PAGE\s+\d+\s+---",
    ]
    for patron in patrones:
        texto = re.sub(patron, "", texto)
    return texto


def parsear_examen_universal(archivo_pdf: Any) -> list[dict[str, str]]:
    preguntas_extraidas: list[dict[str, str]] = []
    texto_total = ""

    with pdfplumber.open(archivo_pdf) as pdf:
        for pagina in pdf.pages:
            raw = pagina.extract_text()
            if raw:
                texto_total += limpiar_ruido_general(raw) + "\n"

    bloques = re.split(r"\n\s*(?=\d+[\.\-\)\s]+)", texto_total)

    for bloque in bloques:
        if not bloque.strip():
            continue

        match_enunciado = re.split(r"\n\s*(?=[aA][\.\-\)\s])", bloque, maxsplit=1)
        if len(match_enunciado) < 2:
            continue

        enunciado_raw = match_enunciado[0]
        resto = match_enunciado[1]
        enunciado = re.sub(r"^\d+[\.\-\)\s]+", "", enunciado_raw).strip()

        match_b = re.split(r"\n\s*(?=[bB][\.\-\)\s])", resto, maxsplit=1)
        if len(match_b) < 2:
            continue

        op_a = match_b[0].strip()
        match_c = re.split(r"\n\s*(?=[cC][\.\-\)\s])", match_b[1], maxsplit=1)
        if len(match_c) < 2:
            continue

        op_b = match_c[0].strip()
        op_c = match_c[1].strip()

        op_a = re.sub(r"^[aA][\.\-\)\s]+", "", op_a).strip()
        op_b = re.sub(r"^[bB][\.\-\)\s]+", "", op_b).strip()
        op_c = re.sub(r"^[cC][\.\-\)\s]+", "", op_c).strip()

        preguntas_extraidas.append(
            {
                "Enunciado": enunciado.replace("\n", " "),
                "opcion_a": op_a.replace("\n", " "),
                "opcion_b": op_b.replace("\n", " "),
                "opcion_c": op_c.replace("\n", " "),
                "correcta": "A",
                "Explicación": "",
                "Tema": "",
            }
        )

    return preguntas_extraidas
