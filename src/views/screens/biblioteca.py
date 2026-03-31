"""Library screen renderer - Optimizado para Móvil y Tabs."""

from __future__ import annotations
from typing import Any, Callable
import pandas as pd
import streamlit as st

def render_biblioteca_screen(
    *,
    supabase: Any,
    limpiar_estado_maestro: Callable[[], None],
    cambiar_vista: Callable[[str], None],
) -> None:
    """Renderizado de biblioteca adaptable a móvil."""
    
    # Eliminamos el 'if sub_pantalla' para que el Tab siempre pinte el contenido
    st.markdown('<div class="titulo-pantalla">📚 BIBLIOTECA</div>', unsafe_allow_html=True)

    # 1. CARGA DE DATOS
    try:
        # Nota: He mantenido el nombre de tu tabla "biblioteca" y columna "name" según tu código
        res = supabase.table("biblioteca").select("*").order("orden").execute()
        df_biblio = pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        df_biblio = pd.DataFrame()

    # 2. BUSCADOR (Elemento clave en móvil)
    busqueda = st.text_input(
        "🔍 Buscar normativa...",
        placeholder="Ej: Constitución, Contratos...",
        key="input_buscador_biblio",
    )

    df_mostrar = df_biblio.copy()
    if busqueda and not df_biblio.empty:
        df_mostrar = df_biblio[df_biblio["name"].str.contains(busqueda, case=False, na=False)]

    # 3. INTERFAZ MÓVIL (Tarjetas vs Tabla)
    if df_mostrar.empty:
        st.info("No se han encontrado leyes.")
    else:
        # En móvil, es mejor listar tarjetas expandibles que una tabla ancha
        for _, ley in df_mostrar.iterrows():
            with st.expander(f"📄 {ley['name']}"):                
                # Acciones de la Ley
                c1, c2 = st.columns(2)
                with c1:
                    if ley["url_pdf"]:
                        st.link_button("📥 VER PDF", ley["url_pdf"], width='stretch')
                    else:
                        st.caption("PDF no disponible")
                
                # Lógica para Admin dentro de la propia tarjeta
                if st.session_state.get("user_role") == "admin":
                    with c2:
                        if st.button("🗑️ ELIMINAR", key=f"del_{ley['id']}", width='stretch', type="secondary"):
                            supabase.table("biblioteca").delete().eq("id", ley['id']).execute()
                            st.toast("Registro eliminado")
                            st.rerun()

    # 4. SECCIÓN ADMIN: AÑADIR NUEVA LEY
    if st.session_state.get("user_role") == "admin":
        st.divider()
        with st.expander("➕ AÑADIR NUEVA NORMATIVA"):
            with st.form("form_nueva_ley_biblio", clear_on_submit=True):
                nuevo_nombre = st.text_input("Nombre de la Ley")
                nueva_url = st.text_input("URL del PDF")
                siguiente_orden = int(df_biblio["orden"].max() + 1) if not df_biblio.empty else 1
                nuevo_orden = st.number_input("Orden", value=siguiente_orden)

                if st.form_submit_button("GUARDAR EN BIBLIOTECA", width='stretch'):
                    if nuevo_nombre:
                        nueva_data = {"name": nuevo_nombre, "url_pdf": nueva_url, "orden": nuevo_orden}
                        supabase.table("biblioteca").insert(nueva_data).execute()
                        st.rerun()
                    else:
                        st.error("El nombre es obligatorio.")