import time

import streamlit as st

from src.views.components.pregunta_form import renderizar_formulario_edicion_pregunta


@st.dialog("🎯 Revisión y Respuesta", width="large")
def modal_responder_feedback(ticket, supabase):
    res_p = supabase.table("preguntas").select("*").eq("id", ticket["pregunta_id"]).single().execute()
    p = res_p.data

    res_t = supabase.table("temas").select("id, nombre").execute()
    temas_db = res_t.data if res_t.data else []
    temas_nombres = [t["nombre"] for t in temas_db]
    temas_dict = {t["nombre"]: t["id"] for t in temas_db}
    id_a_nombre = {t["id"]: t["nombre"] for t in temas_db}

    p["tema_nombre"] = id_a_nombre.get(p.get("tema_id"), "")

    st.warning(f"📩 **MENSAJE DEL USUARIO:** {ticket['mensaje_usuario']}")
    st.write("---")

    st.subheader("🛠️ Editar Pregunta (si procede)")
    f_enun, f_exp, f_a, f_b, f_c, f_corr, f_tema_nom = renderizar_formulario_edicion_pregunta(p, temas_nombres)

    st.write("---")

    st.subheader("✉️ Tu Respuesta al Alumno")
    respuesta_adm = st.text_area("Explícale por qué tiene razón (o por qué no):", height=100, key=f"resp_{ticket['id']}")

    estado = st.selectbox("Estado final:", ["pendiente", "revisado", "corregido", "descartado"], index=1)

    if st.button("💾 GUARDAR CAMBIOS Y NOTIFICAR ALUMNO", type="primary", use_container_width=True):
        if not respuesta_adm:
            st.error("Por favor, escribe una respuesta para el alumno antes de cerrar.")
            return

        try:
            with st.spinner("Procesando cambios..."):
                data_pregunta = {
                    "enunciado": f_enun,
                    "explicacion": f_exp,
                    "opcion_a": f_a,
                    "opcion_b": f_b,
                    "opcion_c": f_c,
                    "correcta": f_corr,
                    "tema_id": temas_dict.get(f_tema_nom),
                }
                supabase.table("preguntas").update(data_pregunta).eq("id", p["id"]).execute()

                data_ticket = {
                    "respuesta_admin": respuesta_adm,
                    "estado": estado,
                    "leido_por_usuario": False,
                }
                supabase.table("feedback_tickets").update(data_ticket).eq("id", ticket["id"]).execute()

            st.success("✅ Pregunta actualizada y respuesta enviada.")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Error en la actualización: {e}")


def render_admin_feedback_screen(supabase):
    st.markdown('<div class="titulo-pantalla">📥 Feedback de Usuarios</div>', unsafe_allow_html=True)

    res = supabase.table("feedback_tickets").select("*").order("created_at", desc=True).execute()
    tickets = res.data if res.data else []

    if not tickets:
        st.info("No hay mensajes de feedback por el momento.")
        return

    t_pendientes, t_historial = st.tabs(["🔴", "⚪"])

    with t_pendientes:
        pendientes = [t for t in tickets if t["estado"] == "pendiente"]
        if not pendientes:
            st.success("¡Buen trabajo! No hay dudas pendientes.")
        for t in pendientes:
            with st.container(border=True):
                c1, c2 = st.columns([0.8, 0.2])
                with c1:
                    st.write(f"**Pregunta ID:** `{t['pregunta_id']}`")
                    st.write(f"_{t['mensaje_usuario']}_")
                with c2:
                    if st.button("Responder", key=f"btn_p_{t['id']}", use_container_width=True):
                        modal_responder_feedback(t, supabase)

    with t_historial:
        for t in tickets:
            color_label = "🟢" if t["estado"] in ["revisado", "corregido"] else "⚪"
            with st.expander(f"{color_label} Ticket #{t['id']} - Pregunta {t['pregunta_id']} ({t['estado']})"):
                st.write(f"**Alumno:** {t['mensaje_usuario']}")
                if t["respuesta_admin"]:
                    st.markdown(f"**Tu respuesta:** {t['respuesta_admin']}")
                else:
                    if st.button("Escribir respuesta", key=f"btn_h_{t['id']}"):
                        modal_responder_feedback(t, supabase)
