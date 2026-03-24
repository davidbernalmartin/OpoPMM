"""Business logic for exam evaluation and persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExamResult:
    total: int
    aciertos: int
    fallos: int
    blancos: int
    nota: float
    errores: list[dict[str, Any]]


def calculate_exam_result(
    preguntas: list[dict[str, Any]], respuestas_usuario: dict[int, str], user_id: str
) -> ExamResult:
    aciertos = 0
    fallos = 0
    blancos = 0
    lista_errores: list[dict[str, Any]] = []

    for i, pregunta in enumerate(preguntas):
        resp = respuestas_usuario.get(i)
        correcta = str(pregunta["correcta"]).upper().strip()

        if resp is None:
            blancos += 1
        elif resp == correcta:
            aciertos += 1
        else:
            fallos += 1
            lista_errores.append(
                {
                    "user_id": user_id,
                    "tema_id": pregunta.get("tema_id"),
                    "pregunta_id": pregunta.get("id"),
                }
            )

    total = len(preguntas)
    nota = (aciertos - (fallos / 3)) * (10 / total) if total > 0 else 0
    nota = max(0, round(nota, 2))

    return ExamResult(
        total=total,
        aciertos=aciertos,
        fallos=fallos,
        blancos=blancos,
        nota=nota,
        errores=lista_errores,
    )


def persist_exam_result(supabase: Any, user_id: str, exam_type: str, result: ExamResult) -> None:
    """Persist exam summary and related wrong answers in Supabase."""
    res_h = (
        supabase.table("historial_examenes")
        .insert(
            {
                "user_id": user_id,
                "tipo_examen": exam_type,
                "num_preguntas": result.total,
                "aciertos": result.aciertos,
                "fallos": result.fallos,
                "blancos": result.blancos,
                "nota_final": result.nota,
            }
        )
        .execute()
    )

    if result.fallos > 0 and res_h.data:
        examen_id = res_h.data[0]["id"]
        errores = [{**error, "examen_id": examen_id} for error in result.errores]
        supabase.table("errores_usuario").insert(errores).execute()