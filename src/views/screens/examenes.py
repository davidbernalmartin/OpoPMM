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
) -> None:
    """
    Renderizado principal de la sección de exámenes adaptado para TABS.
    """
    # Si no hay un paso de configuración definido, empezamos por los botones
    if "paso_configuracion" not in st.session_state or st.session_state.paso_configuracion is None:
        st.session_state.paso_configuracion = "botones"

    # 1. FLUJO DE CONFIGURACIÓN (Antes de generar las preguntas)
    if st.session_state.sub_pantalla not in ["test_ingles", "test_por_temas", "test_simulacro"]:
        _render_selector_modo_examen(supabase)
    
    # 2. GENERACIÓN DE EXAMEN (Cuando ya hemos elegido cantidad/temas)
    elif st.session_state.sub_pantalla == "test_ingles":
        _render_test_ingles(supabase, mostrar_examen, navegar_a)

    elif st.session_state.sub_pantalla == "test_por_temas":
        _render_test_por_temas(supabase, mostrar_examen, navegar_a)

    elif st.session_state.sub_pantalla == "test_simulacro":
        _render_test_simulacro(supabase, mostrar_examen, navegar_a)


def _render_selector_modo_examen(supabase: Any) -> None:
    # Aseguramos que los botones siempre tengan width='stretch' para móvil
    
    if st.session_state.paso_configuracion == "botones":
        st.markdown('<div class="titulo-pantalla">MODO EXAMEN</div>', unsafe_allow_html=True)
        
        # Usamos columnas que no se apilen tan agresivamente
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🇬🇧\n\nINGLÉS", width='stretch'):
                st.session_state.modo_seleccionado = "ingles"
                st.session_state.paso_configuracion = "seleccion_cantidad"
                st.rerun()
        with col2:
            if st.button("📚\n\nTEMAS", width='stretch'):
                st.session_state.modo_seleccionado = "por_temas"
                st.session_state.paso_configuracion = "seleccion_temas"
                st.rerun()
        with col3:
            if st.button("⏱️\n\nSIMULACRO", width='stretch'):
                st.session_state.modo_seleccionado = "simulacro"
                st.session_state.paso_configuracion = "seleccion_cantidad"
                st.rerun()

    elif st.session_state.paso_configuracion == "seleccion_temas":
        st.markdown('<div class="titulo-pantalla">SELECCION DE TEMAS</div>', unsafe_allow_html=True)
        try:
            res = supabase.table("temas").select("id, nombre").order("id").neq("id", 1).execute()
            opciones = {f"Tema {t['nombre']}": t["id"] for t in res.data}
            seleccion = st.multiselect("Selecciona leyes:", options=list(opciones.keys()))

            st.write("---")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("⬅️ VOLVER", width='stretch'):
                    st.session_state.paso_configuracion = "botones"
                    st.rerun()
            with c2:
                if st.button("CONTINUAR ➡️", type="primary", width='stretch', disabled=not seleccion):
                    st.session_state.temas_seleccionados = [opciones[s] for s in seleccion]
                    st.session_state.paso_configuracion = "seleccion_cantidad"
                    st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    elif st.session_state.paso_configuracion == "seleccion_cantidad":
        st.markdown('<div class="titulo-pantalla">Nº PREGUNTAS</div>', unsafe_allow_html=True)
        st.info(f"Modo seleccionado: **{st.session_state.modo_seleccionado.upper()}**")

        cantidad = st.select_slider("Cantidad:", options=[10, 20, 40, 80, 100], value=20)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅️ VOLVER", width='stretch'):
                st.session_state.paso_configuracion = "por_temas" if st.session_state.modo_seleccionado == "por_temas" else "botones"
                st.rerun()
        with c2:
            if st.button("🚀 EMPEZAR", type="primary", width='stretch'):
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
