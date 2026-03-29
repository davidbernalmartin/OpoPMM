"""Helpers to initialize and cleanup Streamlit session state."""

from __future__ import annotations

DEFAULT_SESSION_VALUES = {
    "sub_pantalla": "inicio",
    "user": None,
    "user_role": "invitado",
    "temas_seleccionados": [],
    "examen_iniciado": "NO",
    "preguntas_examen": [],
    "indice_pregunta": 0,
    "respuestas_usuario": {},
    "examen_finalizado": False,
    "configurando_examen": False,
    "modo_seleccionado": None,
    "modo_creacion_pregunta": False,
    "paso_configuracion": "botones",
    "preguntas_pendientes": [],
    "mostrando_revision": False,
}


RESETTABLE_KEYS = [
    "preguntas_examen",
    "respuestas",
    "tipo_test_actual",
    "nota_ultima",
    "preguntas",
    "respuestas_usuario",
    "test_finalizado",
    "pregunta_actual",
    "preguntas_pendientes",
    "temas_seleccionados",
    "num_preguntas_test",
    "error_importacion",
    "test_generado",
    "paso_configuracion",
]


UPLOAD_WIDGET_KEYS = ["uploader_pdf_modal", "uploader_modal"]


def ensure_defaults(session_state: dict) -> None:
    """Initialize required keys with default values only if missing."""
    for key, value in DEFAULT_SESSION_VALUES.items():
        session_state.setdefault(key, value)


def reset_exam_state(session_state: dict) -> None:
    """Reset exam-related state while preserving auth/profile context."""
    for key in RESETTABLE_KEYS:
        if key not in session_state:
            continue
        if key in {"preguntas", "preguntas_pendientes", "temas_seleccionados"}:
            session_state[key] = []
        elif key in {"respuestas_usuario", "respuestas"}:
            session_state[key] = {}
        elif key in {"pregunta_actual", "num_preguntas_test"}:
            session_state[key] = 0
        elif key in {"test_finalizado", "test_generado"}:
            session_state[key] = False
        else:
            del session_state[key]

    for widget_key in UPLOAD_WIDGET_KEYS:
        if widget_key in session_state:
            del session_state[widget_key]