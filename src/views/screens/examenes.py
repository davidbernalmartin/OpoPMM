"""Exam flow screens for Streamlit app."""

from __future__ import annotations

import random
from typing import Any, Callable

import streamlit as st


def render_examenes_screen(
    *,
    supabase: Any,
    mostrar_examen: Callable[[str, list[dict[str, Any]]], None],
    navegar_a: Callable[[str], None],
) -> bool:
    """
    Render exam-related screens.

    Returns True if current `sub_pantalla` was handled.
    """
    sub_pantalla = st.session_state.sub_pantalla

    if sub_pantalla == "seleccion_tema":
        _render_selector_modo_examen(supabase)
        return True

    if sub_pantalla == "test_ingles":
        _render_test_ingles(supabase, mostrar_examen, navegar_a)
        return True

    if sub_pantalla == "test_por_temas":
        _render_test_por_temas(supabase, mostrar_examen, navegar_a)
        return True

    if sub_pantalla == "test_simulacro":
        _render_test_simulacro(supabase, mostrar_examen, navegar_a)
        return True

    return False


def _render_selector_modo_examen(supabase: Any) -> None:
    if st.session_state.paso_configuracion == "botones":
        st.markdown('<div class="titulo-pantalla">MODO EXAMEN</div>', unsafe_allow_html=True)
        st.markdown('<div class="contenedor-test">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🇬🇧\n\nEXAMEN DE INGLÉS", use_container_width=True):
                st.session_state.modo_seleccionado = "ingles"
                st.session_state.paso_configuracion = "seleccion_cantidad"
                st.rerun()
        with col2:
            if st.button("📚\n\nEXAMEN POR TEMAS", use_container_width=True):
                st.session_state.modo_seleccionado = "por_temas"
                st.session_state.paso_configuracion = "seleccion_temas"
                st.rerun()
        with col3:
            if st.button("⏱️\n\nSIMULACRO EXAMEN", use_container_width=True):
                st.session_state.modo_seleccionado = "simulacro"
                st.session_state.paso_configuracion = "seleccion_cantidad"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state.paso_configuracion == "seleccion_temas":
        st.markdown('<div class="titulo-pantalla">SELECCION DE TEMAS</div>', unsafe_allow_html=True)
        try:
            res = supabase.table("temas").select("id, nombre").order("id").neq("id", 1).execute()
            temas_db = res.data
            opciones = {f"Tema {t['nombre']}": t["id"] for t in temas_db if t["id"] != 1}
            seleccion = st.multiselect("Selecciona una o varias leyes:", options=list(opciones.keys()))

            st.write("---")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("⬅️ VOLVER", use_container_width=True):
                    st.session_state.paso_configuracion = "botones"
                    st.rerun()
            with c2:
                if st.button("CONTINUAR ➡️", type="primary", use_container_width=True, disabled=not seleccion):
                    st.session_state.temas_seleccionados = [opciones[s] for s in seleccion]
                    st.session_state.paso_configuracion = "seleccion_cantidad"
                    st.rerun()
        except Exception as e:
            st.error(f"Error cargando temas: {e}")

    elif st.session_state.paso_configuracion == "seleccion_cantidad":
        st.markdown('<div class="titulo-pantalla">NUMERO DE PREGUNTAS</div>', unsafe_allow_html=True)
        st.write(f"Modo: **{st.session_state.modo_seleccionado.upper()}**")

        cantidad = st.select_slider(
            "¿Cuántas preguntas quieres responder?",
            options=[10, 20, 40, 80, 100],
            value=20,
        )

        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅️ VOLVER", use_container_width=True):
                if st.session_state.modo_seleccionado == "por_temas":
                    st.session_state.paso_configuracion = "seleccion_temas"
                else:
                    st.session_state.paso_configuracion = "botones"
                st.rerun()
        with c2:
            if st.button("🚀 EMPEZAR EXAMEN", type="primary", use_container_width=True):
                st.session_state.cantidad_preguntas = cantidad
                st.session_state.sub_pantalla = f"test_{st.session_state.modo_seleccionado}"
                st.rerun()


def _render_test_ingles(supabase: Any, mostrar_examen: Callable, navegar_a: Callable[[str], None]) -> None:
    if not st.session_state.preguntas_examen:
        limite_elegido = st.session_state.get("cantidad_preguntas", 20)
        st.session_state.tipo_test_actual = "ingles"
        try:
            res = supabase.table("preguntas").select("*").eq("tema_id", 1).execute()
            if res.data:
                todo_el_banco = res.data
                random.shuffle(todo_el_banco)
                st.session_state.preguntas_examen = todo_el_banco[:limite_elegido]
                st.session_state.indice_pregunta = 0
                st.session_state.respuestas_usuario = {}
                st.session_state.examen_finalizado = False
                st.rerun()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            if st.button("Volver al menú"):
                navegar_a("botones")

    if st.session_state.preguntas_examen:
        mostrar_examen("EXAMEN DE INGLÉS", st.session_state.preguntas_examen)


def _render_test_por_temas(
    supabase: Any, mostrar_examen: Callable, navegar_a: Callable[[str], None]
) -> None:
    if not st.session_state.preguntas_examen:
        ids_seleccionados = st.session_state.get("temas_seleccionados", [])
        limite_elegido = st.session_state.get("cantidad_preguntas", 20)
        st.session_state.tipo_test_actual = "temas"
        try:
            res = supabase.table("preguntas").select("*").in_("tema_id", ids_seleccionados).execute()
            if res.data:
                todo_el_banco = res.data
                random.shuffle(todo_el_banco)
                st.session_state.preguntas_examen = todo_el_banco[:limite_elegido]
                st.session_state.indice_pregunta = 0
                st.session_state.respuestas_usuario = {}
                st.session_state.examen_finalizado = False
                st.rerun()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            if st.button("Volver al menú"):
                navegar_a("botones")

    if st.session_state.preguntas_examen:
        mostrar_examen("EXAMEN POR TEMAS", st.session_state.preguntas_examen)


def _render_test_simulacro(
    supabase: Any, mostrar_examen: Callable, navegar_a: Callable[[str], None]
) -> None:
    if not st.session_state.preguntas_examen:
        limite_elegido = st.session_state.get("cantidad_preguntas", 20)
        st.session_state.tipo_test_actual = "simulacro"
        try:
            res = supabase.table("preguntas").select("*").neq("tema_id", 1).execute()
            if res.data:
                todo_el_banco = res.data
                random.shuffle(todo_el_banco)
                st.session_state.preguntas_examen = todo_el_banco[:limite_elegido]
                st.session_state.indice_pregunta = 0
                st.session_state.respuestas_usuario = {}
                st.session_state.examen_finalizado = False
                st.rerun()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            if st.button("Volver al menú"):
                navegar_a("botones")

    if st.session_state.preguntas_examen:
        mostrar_examen("SIMULACRO GENERAL", st.session_state.preguntas_examen)
