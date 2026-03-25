"""Library screen renderer."""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd
import streamlit as st


def render_biblioteca_screen(
    *,
    supabase: Any,
    limpiar_estado_maestro: Callable[[], None],
    cambiar_vista: Callable[[str], None],
) -> bool:
    """Render library screen. Returns True when handled."""
    if st.session_state.sub_pantalla != "biblioteca":
        return False

    st.markdown('<div class="titulo-pantalla">📚 BIBLIOTECA LEGISLATIVA</div>', unsafe_allow_html=True)

    try:
        res = supabase.table("biblioteca").select("*").order("orden").execute()
        df_biblio = pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        df_biblio = pd.DataFrame()

    df_mostrar = df_biblio.copy()

    st.write("### 🔍 Buscar Normativa")
    busqueda = st.text_input(
        "Introduce el nombre de la ley...",
        placeholder="Ej: Constitución, Contratos, Procedimiento...",
        label_visibility="collapsed",
        key="input_buscador_biblio",
    )

    if busqueda and not df_biblio.empty:
        df_mostrar = df_biblio[df_biblio["name"].str.contains(busqueda, case=False, na=False)]

    col_tabla, col_gestion = st.columns([0.65, 0.35])

    with col_tabla:
        if not df_mostrar.empty:
            event_biblio = st.dataframe(
                df_mostrar,
                column_order=("orden", "name"),
                column_config={
                    "orden": st.column_config.NumberColumn("Nº"),
                    "name": st.column_config.TextColumn("LEY / NORMA", width="900"),
                },
                hide_index=True,
                width='stretch',
                on_select="rerun",
                selection_mode="single-row",
                key="tabla_biblioteca",
            )
            seleccion_indices = event_biblio.selection.rows
        else:
            st.info("No se han encontrado leyes que coincidan con tu búsqueda.")
            seleccion_indices = []

    with col_gestion:
        if st.session_state.user_role == "admin":
            tab_ver, tab_nuevo = st.tabs(["🔍 Ver Ley", "➕ Añadir Nueva"])

            with tab_ver:
                if seleccion_indices:
                    ley_sel = df_mostrar.iloc[seleccion_indices[0]]
                    st.success(f"**Seleccionada:**\n{ley_sel['name']}")

                    if ley_sel["url_pdf"]:
                        st.link_button("📥 DESCARGAR / VER PDF", ley_sel["url_pdf"], width='stretch')
                    else:
                        st.warning("No hay URL configurada.")

                    st.divider()
                    if st.button("🗑️ ELIMINAR REGISTRO", width='stretch', type="secondary"):
                        supabase.table("biblioteca").delete().eq("id", ley_sel["id"]).execute()
                        st.success("Registro eliminado.")
                        st.rerun()
                else:
                    st.write("Selecciona una fila para gestionar.")

            with tab_nuevo:
                st.write("### Nuevo Registro")
                with st.form("form_nueva_ley_biblio", clear_on_submit=True):
                    nuevo_nombre = st.text_input("Nombre de la Ley")
                    nueva_url = st.text_input("URL del PDF (Enlace directo)")
                    siguiente_orden = int(df_biblio["orden"].max() + 1) if not df_biblio.empty else 1
                    nuevo_orden = st.number_input("Orden", value=siguiente_orden)

                    if st.form_submit_button("AÑADIR A BIBLIOTECA", width='stretch'):
                        if nuevo_nombre:
                            nueva_data = {"name": nuevo_nombre, "url_pdf": nueva_url, "orden": nuevo_orden}
                            supabase.table("biblioteca").insert(nueva_data).execute()
                            st.rerun()
                        else:
                            st.error("El nombre es obligatorio.")
        else:
            st.markdown("### 📄 Detalles")
            if seleccion_indices:
                ley_sel = df_mostrar.iloc[seleccion_indices[0]]
                st.info(f"**Normativa:**\n{ley_sel['name']}")
                if ley_sel["url_pdf"]:
                    st.link_button("📥 DESCARGAR / VER PDF", ley_sel["url_pdf"], width='stretch')
                else:
                    st.warning("Documento no disponible.")
            else:
                st.write("Selecciona una ley de la lista para ver el enlace de descarga.")

    st.write("---")
    if st.button("⬅️ VOLVER AL MENÚ", key="btn_volver_biblio"):
        limpiar_estado_maestro()
        cambiar_vista("menu_principal")
        st.rerun()

    return True
