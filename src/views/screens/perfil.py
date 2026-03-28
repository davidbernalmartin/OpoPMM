"""Profile screen renderer."""

from __future__ import annotations
from typing import Any
import streamlit as st

def render_perfil_screen(*, supabase: Any) -> None:
    """Render profile screen optimizado para Tabs."""
    # ELIMINADO: if st.session_state.sub_pantalla != "perfil": return False

    st.markdown('<div class="titulo-pantalla">MI PERFIL</div>', unsafe_allow_html=True)

    try:
        res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
        datos_perfil = res.data if res.data else {}
    except Exception as e:
        st.error(f"Error al cargar perfil: {e}")
        datos_perfil = {}

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre", value=datos_perfil.get("nombre", ""))
            apellidos = st.text_input("Apellidos", value=datos_perfil.get("apellidos", ""))

        with col2:
            telefono = st.text_input("Teléfono", value=datos_perfil.get("telefono", ""))
            direccion = st.text_input("Dirección", value=datos_perfil.get("direccion", ""))

        ciudad = st.text_input("Ciudad", value=datos_perfil.get("ciudad", ""))

        st.write("---")
        st.write(f"**Email de cuenta:** {st.session_state.user.email}")
        st.write(f"**Rol de usuario:** {st.session_state.user_role.upper()}")

        # Cambio width='stretch' por use_container_width=True para compatibilidad móvil
        if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
            try:
                actualizacion = {
                    "nombre": nombre,
                    "apellidos": apellidos,
                    "telefono": telefono,
                    "direccion": direccion,
                    "ciudad": ciudad,
                }
                supabase.table("profiles").update(actualizacion).eq("id", st.session_state.user.id).execute()
                st.success("¡Perfil actualizado correctamente!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")