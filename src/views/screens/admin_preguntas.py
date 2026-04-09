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
    if c1.button("🔥 SÍ, ELIMINAR", type="primary", width='stretch'):
        with st.spinner("Eliminando..."):
            supabase.table("preguntas").delete().eq("id", pregunta['id']).execute()
        st.success("Pregunta eliminada.")
        st.rerun()
        
    if c2.button("CANCELAR", width='stretch'):
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
    if c1.button("📝 MODIFICAR ESTA PREGUNTA", type="primary", width='stretch'):
        # 1. Guardamos la pregunta en el estado global
        st.session_state.trigger_modal_edicion = pregunta
        # 2. Forzamos rerun: esto cierra este modal y activa el controlador en la pantalla principal
        st.rerun()
        
    if c2.button("CERRAR", width='stretch'):
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
    
    if col_g.button("💾 GUARDAR CAMBIOS", type="primary", width='stretch'):
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

    if col_c.button("❌ CANCELAR", width='stretch'):
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
        c1, c2, c3, c4 = st.columns(4)

        # Mostramos botones de importación aunque no haya datos
        with c1:
            if st.button("➕ NUEVA", type="primary", width='stretch'):
                nueva = {"id": None, "enunciado": "", "opcion_a": "", "opcion_b": "", "opcion_c": "", "correcta": "A", "explicacion": "", "tema_nombre": ""}
                modal_edicion(nueva, supabase, temas_nombres, temas_dict)

        with c2:
            st.button("📄 PDF", width='stretch', on_click=modal_importar_pdf)

        with c3:
            st.button("📊 CSV", width='stretch', on_click=modal_importar)

        with c4:
            if st.button("🗑️ BORRAR", width='stretch', disabled=True):
                modal_eliminar_pregunta(pregunta_sel, supabase)        
        return

    df = pd.DataFrame(data_for_df)

    # --- 4. DATAFRAME Y SELECCIÓN ---
    selection_event = st.dataframe(
        df[["Enunciado", "Tema", "Respuesta"]],
        width='stretch',
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
            if st.button("🔍 PREVISUALIZAR", type="primary", width='stretch'):
                modal_consulta(pregunta_sel)
        else:
            if st.button("➕ NUEVA", type="primary", width='stretch'):
                nueva = {"id": None, "enunciado": "", "opcion_a": "", "opcion_b": "", "opcion_c": "", "correcta": "A", "explicacion": "", "tema_nombre": ""}
                modal_edicion(nueva, supabase, temas_nombres, temas_dict)

    with c2:
        st.button("📄 PDF", width='stretch', on_click=modal_importar_pdf)

    with c3:
        st.button("📊 CSV", width='stretch', on_click=modal_importar)

    with c4:
        if st.button("🗑️ BORRAR", width='stretch', disabled=not hay_sel):
            modal_eliminar_pregunta(pregunta_sel, supabase)

def render_admin_preguntas_screens(**kwargs):
    supabase = kwargs['supabase']
    
    # 1. SIEMPRE obtenemos los temas primero para tener el mapeo ID <-> Nombre
    res_t = supabase.table("temas").select("id, nombre").execute()
    temas_dict = {t["nombre"]: t["id"] for t in res_t.data}

    # 2. Miramos en qué sub-pantalla estamos
    sub_pantalla = st.session_state.get("sub_pantalla")
    
    if sub_pantalla == "revision_importacion":
        # AHORA SÍ: Pasamos supabase Y temas_dict
        _render_pantalla_revision_importar(supabase, temas_dict)
    else:
        _render_admin_preguntas(
            supabase=supabase,
            renderizar_formulario_edicion=kwargs['renderizar_formulario_edicion'],
            modal_importar_pdf=kwargs['modal_importar_pdf'],
            modal_importar=kwargs['modal_importar'],
        )

def _render_pantalla_revision_importar(supabase, temas_dict):
    st.markdown('<div class="titulo-pantalla">REVISIÓN TÁCTICA DE CARGA</div>', unsafe_allow_html=True)
    
    preguntas = st.session_state.get("preguntas_pendientes", [])
    
    if not preguntas:
        st.warning("No hay preguntas en la cola.")
        if st.button("⬅️ VOLVER"):
            st.session_state.sub_pantalla = None
            st.rerun()
        return

    # --- LISTADO DE EXPANDERS ---
    for i in range(len(st.session_state.preguntas_pendientes)):
        p = st.session_state.preguntas_pendientes[i]
        
        # Estado de borrado (si no existe, por defecto es False)
        if 'descartar' not in p:
            st.session_state.preguntas_pendientes[i]['descartar'] = False
        
        descartar = st.session_state.preguntas_pendientes[i]['descartar']
            
        key_p = f"rev_q{i}" # Clave estática porque ya no movemos los índices
        resumen = p.get('enunciado') or p.get('Enunciado', 'Sin texto')
        
        # Color y título dinámico si está descartada
        emoji = "❌ [DESCARTADA]" if p['descartar'] else "📄"
        
        with st.expander(f"{emoji} FICHA #{i+1} | {resumen[:50]}...", expanded=False):
            # --- ESTRUCTURA DE COLUMNAS (Solo editable si no está descartada, para evitar errores) ---
            col_textos = st.columns(2)
            with col_textos[0]:
                st.session_state.preguntas_pendientes[i]['enunciado'] = st.text_area(
                    "📝 ENUNCIADO", value=p.get('enunciado') or p.get('Enunciado', ''), 
                    key=f"enun_{key_p}", height=150, disabled=descartar
                )
            with col_textos[1]:
                st.session_state.preguntas_pendientes[i]['explicacion'] = st.text_area(
                    "⚖️ EXPLICACIÓN", value=p.get('explicacion') or p.get('Explicación', ''), 
                    key=f"exp_{key_p}", height=150, disabled=descartar
                )

            col_izq, col_der = st.columns([3, 2])
            with col_izq:
                st.session_state.preguntas_pendientes[i]['opcion_a'] = st.text_input("🟢 A", value=p.get('opcion_a', ''), key=f"a_{key_p}", disabled=descartar)
                st.session_state.preguntas_pendientes[i]['opcion_b'] = st.text_input("🟡 B", value=p.get('opcion_b', ''), key=f"b_{key_p}", disabled=descartar)
                st.session_state.preguntas_pendientes[i]['opcion_c'] = st.text_input("🔴 C", value=p.get('opcion_c', ''), key=f"c_{key_p}", disabled=descartar)

            with col_der:
                nombres_temas = list(temas_dict.keys())
                ids_temas = list(temas_dict.values())
                tema_id_csv = p.get('tema_id') or p.get('Tema')
                
                idx_tema = 0
                try:
                    t_id = int(tema_id_csv)
                    if t_id in ids_temas: idx_tema = ids_temas.index(t_id)
                except: pass

                tema_sel = st.selectbox("📚 TEMA", nombres_temas, index=idx_tema, key=f"tema_{key_p}", disabled=descartar)
                st.session_state.preguntas_pendientes[i]['tema_id'] = temas_dict.get(tema_sel)
                
                val_corr = str(p.get('correcta', 'A')).upper().strip()
                idx_corr = ["A", "B", "C"].index(val_corr) if val_corr in ["A", "B", "C"] else 0
                st.session_state.preguntas_pendientes[i]['correcta'] = st.selectbox("✅ CORRECTA", ["A", "B", "C"], index=idx_corr, key=f"corr_{key_p}", disabled=descartar)

                # --- CHECKBOX DE BORRADO ---
                # Si se marca, el resto de la ficha se ignora lógicamente
                n_descartar = st.checkbox("🗑️ MARCAR PARA ELIMINAR / NO IMPORTAR", value=descartar, key=f"check_{key_p}")
                if n_descartar != descartar:
                    st.session_state.preguntas_pendientes[i]['descartar'] = n_descartar
                    st.rerun()
                
                if n_descartar:
                    st.error("Esta pregunta NO se guardará en el CSV ni se subirá a la Base de Datos.")

    st.markdown("---")
    
    # --- BOTONES DE ACCIÓN (CON FILTRADO) ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("❌ ABORTAR CARGA", use_container_width=True):
            st.session_state.preguntas_pendientes = []
            st.session_state.sub_pantalla = None
            st.rerun()

    with c2:
        # FILTRADO PARA CSV: Solo las que NO tengan 'descartar' en True
        preguntas_validas = [q for q in st.session_state.preguntas_pendientes if not q.get('descartar')]
        df_export = pd.DataFrame(preguntas_validas)
        # Eliminamos columna auxiliar antes de guardar
        if not df_export.empty and 'descartar' in df_export.columns:
            df_export = df_export.drop(columns=['descartar'])
        
        st.info(df_export)

        csv = df_export.to_csv(index=False, sep=";").encode('utf-8')
        st.download_button("💾 GUARDAR PROGRESO (CSV)", data=csv, file_name="revision_pmm.csv", mime="text/csv", use_container_width=True)

    with c3:
        if st.button("🚀 VOLCAR A BASE DE DATOS", type="primary", use_container_width=True):
            # FILTRADO PARA BD
            preguntas_finales = [q for q in st.session_state.preguntas_pendientes if not q.get('descartar')]
            
            if not preguntas_finales:
                st.error("No hay preguntas válidas para subir (todas marcadas como descartadas).")
            else:
                with st.spinner("Subiendo..."):
                    try:
                        batch = []
                        for q in preguntas_finales:
                            batch.append({
                                "enunciado": q.get('enunciado'),
                                "opcion_a": q.get('opcion_a'),
                                "opcion_b": q.get('opcion_b'),
                                "opcion_c": q.get('opcion_c'),
                                "correcta": q.get('correcta'),
                                "explicacion": q.get('explicacion'),
                                "tema_id": q.get('tema_id')
                            })
                        supabase.table("preguntas").insert(batch).execute()
                        st.success(f"¡Hecho! {len(batch)} preguntas añadidas.")
                        st.session_state.preguntas_pendientes = []
                        st.session_state.sub_pantalla = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")