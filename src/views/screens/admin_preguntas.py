"""Admin question management screens con flujo táctico por Modal."""

from __future__ import annotations
from typing import Any, Callable
import pandas as pd
import streamlit as st

@st.dialog("⚠️ Eliminar Pregunta", width="small")
def modal_eliminar_pregunta(pregunta, supabase):
    st.warning(f"¿Estás seguro de que deseas eliminar permanentemente la pregunta ID: {pregunta['id']}?")
    st.write(f"**Enunciado:** {pregunta['enunciado'][:100]}...")
    
    st.error("Esta acción no se puede deshacer.")
    
    c1, c2 = st.columns(2)
    if c1.button("🔥 SÍ, ELIMINAR", type="primary", use_container_width=True):
        with st.spinner("Eliminando..."):
            supabase.table("preguntas").delete().eq("id", pregunta['id']).execute()
        st.success("Pregunta eliminada.")
        st.rerun()
        
    if c2.button("CANCELAR", use_container_width=True):
        st.rerun()

@st.dialog("🔍 Vista Previa de Pregunta", width="large")
def modal_consulta(pregunta):
    """Muestra la pregunta en verde y activa el trigger de edición al salir."""
    st.markdown(f'<div class="enunciado-container">{pregunta.get("enunciado")}</div>', unsafe_allow_html=True)
    st.write("---")
    
    correcta = str(pregunta.get('correcta', 'A')).upper().strip()
    
    # Renderizado de opciones con resaltado
    for letra in ["A", "B", "C"]:
        texto_opcion = pregunta.get(f'opcion_{letra.lower()}', '')
        es_correcta = letra == correcta
        
        # Definimos el estilo dinámico
        bg_color = "rgba(34, 197, 94, 0.15)" if es_correcta else "rgba(255, 255, 255, 0.03)"
        border_color = "#4ade80" if es_correcta else "transparent"
        text_color = "#4ade80" if es_correcta else "inherit"
        check_mark = " ✅" if es_correcta else ""

        st.markdown(f"""
            <div style="
                background-color: {bg_color}; 
                border-left: 5px solid {border_color}; 
                padding: 12px; 
                border-radius: 5px; 
                margin-bottom: 10px;">
                <span style="color: {text_color}; font-weight: bold;">{letra})</span> {texto_opcion} {check_mark}
            </div>
        """, unsafe_allow_html=True)

# Explicación
    exp = pregunta.get("explicacion")
    if exp and str(exp).strip():
        st.markdown(f'<div class="explicacion-container"><p style="color:#0891B2; font-weight:bold;">💡 EXPLICACIÓN</p>{exp}</div>', unsafe_allow_html=True)
    
    st.divider()
    c1, c2 = st.columns(2)
    
    # --- LA CLAVE DEL POP-UP ENCADENADO ---
    if c1.button("📝 MODIFICAR ESTA PREGUNTA", type="primary", use_container_width=True):
        # 1. Guardamos la pregunta en el estado global
        st.session_state.trigger_modal_edicion = pregunta
        # 2. Forzamos rerun: esto cierra este modal y activa el controlador en la pantalla principal
        st.rerun()
        
    if c2.button("CERRAR", use_container_width=True):
        st.rerun()
    

# --- DIÁLOGO 2: EDICIÓN / CREACIÓN ---
@st.dialog("✏️ Editor de Pregunta", width="large")
def modal_edicion(pregunta, supabase, temas_nombres, temas_dict):
    """Muestra el formulario de edición usando el componente existente."""
    from src.views.components.pregunta_form import renderizar_formulario_edicion_pregunta
    
    st.subheader("Edición de Pregunta" if pregunta.get('id') else "Nueva Pregunta")
    
    # Renderizamos tu formulario
    f_enun, f_exp, f_a, f_b, f_c, f_corr, f_tema_nom = renderizar_formulario_edicion_pregunta(pregunta, temas_nombres)
    
    st.divider()
    col_g, col_c = st.columns(2)
    
    if col_g.button("💾 GUARDAR CAMBIOS", type="primary", use_container_width=True):
        data_save = {
            "enunciado": f_enun,
            "explicacion": f_exp,
            "opcion_a": f_a,
            "opcion_b": f_b,
            "opcion_c": f_c,
            "correcta": f_corr,
            "tema_id": temas_dict.get(f_tema_nom)
        }
        
        with st.spinner("Guardando..."):
            if pregunta.get('id'):
                supabase.table("preguntas").update(data_save).eq("id", pregunta['id']).execute()
            else:
                supabase.table("preguntas").insert(data_save).execute()
        
        st.success("✅ ¡Guardado!")
        st.rerun()

    if col_c.button("❌ CANCELAR", use_container_width=True):
        st.rerun()

def _render_admin_preguntas(supabase, renderizar_formulario_edicion, modal_importar_pdf, modal_importar):
    st.markdown('<div class="titulo-pantalla">🛠️ Gestión</div>', unsafe_allow_html=True)

    # --- 1. CARGA DE DATOS Y TEMAS ---
    res_t = supabase.table("temas").select("id, nombre").execute()
    temas_nombres = [t["nombre"] for t in res_t.data]
    temas_dict = {t["nombre"]: t["id"] for t in res_t.data}

    if "trigger_modal_edicion" in st.session_state:
        p_a_editar = st.session_state.trigger_modal_edicion
        del st.session_state.trigger_modal_edicion # Limpiamos para que no se repita
        modal_edicion(p_a_editar, supabase, temas_nombres, temas_dict)
        
    # --- 2. FILTROS (Nueva Sección) ---
    with st.container():
        c_f1, c_f2 = st.columns([2, 1])
        with c_f1:
            filtro_texto = st.text_input("🔍 Buscar por enunciado...", placeholder="Escribe para filtrar...", key="filter_text")
        with c_f2:
            opciones_temas = ["📂 Todos los temas"] + temas_nombres
            filtro_tema = st.selectbox("🎯 Filtrar por Tema", opciones_temas, key="filter_tema")

    # --- 3. OBTENCIÓN Y FILTRADO DE DATOS ---
    res = supabase.table("preguntas").select("*, temas(nombre)").order("id", desc=True).execute()
    
    if not res.data:
        st.info("No hay preguntas.")
        return

    data_for_df = []
    for r in res.data:
        nombre_tema = r.get("temas", {}).get("nombre", "Sin tema")
        
        # Aplicamos la lógica de filtrado antes de añadir al DataFrame
        match_texto = filtro_texto.lower() in r["enunciado"].lower()
        match_tema = filtro_tema == "📂 Todos los temas" or filtro_tema == nombre_tema
        
        if match_texto and match_tema:
            data_for_df.append({
                "id": r["id"],
                "Tema": nombre_tema,
                "Enunciado": r["enunciado"],
                "Respuesta": r["correcta"],
                "enunciado": r["enunciado"],
                "opcion_a": r["opcion_a"],
                "opcion_b": r["opcion_b"],
                "opcion_c": r["opcion_c"],
                "correcta": r["correcta"],
                "explicacion": r["explicacion"],
                "tema_nombre": nombre_tema
            })

    if not data_for_df:
        st.warning("No hay preguntas que coincidan con los filtros seleccionados.")
        # Mostramos botones de importación aunque no haya datos
        _render_botones_accion(None, None, None, modal_importar_pdf, modal_importar)
        return

    df = pd.DataFrame(data_for_df)

    # --- 4. DATAFRAME Y SELECCIÓN ---
    selection_event = st.dataframe(
        df[["Enunciado", "Tema", "Respuesta"]],
        use_container_width=True,
        hide_index=False,
        on_select="rerun",
        selection_mode="single-row"
    )

    st.write("---")

    # 3. FILA DE ACCIONES (4 Columnas ahora)
    # --- FILA DE ACCIONES INTEGRADA ---
    c1, c2, c3, c4 = st.columns(4)

    hay_sel = len(selection_event.selection.rows) > 0
    pregunta_sel = data_for_df[selection_event.selection.rows[0]] if hay_sel else None

    with c1:
        if hay_sel:
            if st.button("🔍 PREVISUALIZAR", type="primary", use_container_width=True):
                modal_consulta(pregunta_sel)
        else:
            if st.button("➕ NUEVA", type="primary", use_container_width=True):
                nueva = {"id": None, "enunciado": "", "opcion_a": "", "opcion_b": "", "opcion_c": "", "correcta": "A", "explicacion": "", "tema_nombre": ""}
                modal_edicion(nueva, supabase, temas_nombres, temas_dict)

    with c2:
        st.button("📄 PDF", use_container_width=True, on_click=modal_importar_pdf)

    with c3:
        st.button("📊 CSV", use_container_width=True, on_click=modal_importar)

    with c4:
        if st.button("🗑️ BORRAR", use_container_width=True, disabled=not hay_sel):
            modal_eliminar_pregunta(pregunta_sel, supabase)

# Mantenemos la función de entrada principal igual
def render_admin_preguntas_screens(**kwargs):
    # (Lógica de sub_pantalla revision_importacion...)
    if st.session_state.get("sub_pantalla") == "revision_importacion":
        # render revision...
        pass
    else:
        _render_admin_preguntas(
            supabase=kwargs['supabase'],
            renderizar_formulario_edicion=kwargs['renderizar_formulario_edicion'],
            modal_importar_pdf=kwargs['modal_importar_pdf'],
            modal_importar=kwargs['modal_importar'],
        )