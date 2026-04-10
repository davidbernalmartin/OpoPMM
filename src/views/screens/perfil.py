"""Profile screen renderer."""

from __future__ import annotations
from typing import Any
import streamlit as st

# --- src/views/screens/perfil.py ---

@st.dialog("📬 Mi Buzón de Consultas", width="large")
def modal_mis_consultas(supabase, user_id):
    # Consultar tickets del usuario
    res = supabase.table("feedback_tickets")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .execute()
    
    tickets = res.data if res.data else []

    if not tickets:
        st.info("No tienes consultas registradas actualmente.")
        if st.button("CERRAR"): st.rerun()
        return

    # Contenedor con scroll para no romper el diálogo si hay muchos
    container = st.container(height=500, border=False)
    
    with container:
        for t in tickets:
            es_nuevo = not t["leido_por_usuario"] and t["respuesta_admin"]
            
            # Encabezado del Ticket
            with st.container(border=True):
                col_info, col_status = st.columns([0.7, 0.3])
                with col_info:
                    st.markdown(f"**Pregunta ID:** `{t['pregunta_id']}`")
                    st.caption(f"Enviado el: {t['created_at'][:10]}")
                with col_status:
                    if t["estado"] == "pendiente":
                        st.warning("⏳ Pendiente")
                    elif t["estado"] == "corregido":
                        st.success("🛠️ Corregido")
                    else:
                        st.info("✅ Revisado")

                st.markdown(f"**Tu duda:**\n{t['mensaje_usuario']}")

                # Bloque de respuesta si existe
                if t["respuesta_admin"]:
                    st.markdown(f"""
                        <div style="background-color: rgba(8, 145, 178, 0.1); padding: 12px; border-radius: 8px; border-left: 4px solid #0891B2; margin: 10px 0;">
                            <p style="color:#0891B2; font-weight:bold; margin-bottom:5px; font-size: 0.9rem;">👨‍🏫 RESPUESTA ACADEMIA:</p>
                            <p style="font-size: 0.95rem; margin:0;">{t['respuesta_admin']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if es_nuevo:
                        if st.button("Marcar como leído", key=f"read_{t['id']}", use_container_width=True):
                            supabase.table("feedback_tickets").update({"leido_por_usuario": True}).eq("id", t["id"]).execute()
                            st.rerun()
                else:
                    st.caption("🔍 Un profesor revisará tu duda pronto.")

    if st.button("SALIR", use_container_width=True):
        st.rerun()

def render_perfil_screen(*, supabase: Any) -> None:
    """Render profile screen optimizado para Tabs."""

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

        col3, col4 = st.columns(2)
        with col3:
            res_count = supabase.table("feedback_tickets")\
                .select("id", count='exact')\
                .eq("user_id", st.session_state.user.id)\
                .eq("leido_por_usuario", False)\
                .not_.is_("respuesta_admin", "null")\
                .execute()
            
            n_mensajes = res_count.count if res_count.count else 0

            # Si hay mensajes, el botón es "primary" y tiene un emoji de aviso
            label = f"📬 Ver mis mensajes ({n_mensajes})" if n_mensajes > 0 else "📬 Ver mis mensajes"
            tipo = "primary" if n_mensajes > 0 else "secondary"
            
            if st.button(label, type=tipo, use_container_width=True):
                modal_mis_consultas(supabase, st.session_state.user.id)
        with col4:  
            if st.button("💾 GUARDAR CAMBIOS", width='stretch', type="primary"):
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
