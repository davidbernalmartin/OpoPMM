import streamlit as st

def render_historial_screen(supabase, mostrar_examen):
    st.markdown('<div class="titulo-pantalla">MIS EXÁMENES ANTIGUOS</div>', unsafe_allow_html=True)
    
    res = supabase.table("historial_examenes")\
        .select("*")\
        .eq("user_id", st.session_state.user.id)\
        .order("created_at", desc=True)\
        .execute()
    
    if not res.data:
        st.info("Aún no has realizado ningún examen.")
        return

    for examen in res.data:
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            fecha = examen['created_at'][:10] # Formato YYYY-MM-DD
            col1.write(f"📅 **{fecha}** - {examen['tipo_examen'].upper()}")
            col2.write(f"Nota: **{examen['nota_final']}**")
            
            if col3.button("REPASAR", key=f"btn_{examen['id']}"):
                # RECONSTRUCCIÓN DEL EXAMEN:
                # 1. Buscamos las preguntas originales por sus IDs
                res_p = supabase.table("preguntas")\
                    .select("*")\
                    .in_("id", examen['preguntas_ids'])\
                    .execute()
                
                # 2. Reordenar las preguntas según el orden original del examen
                preguntas_dict = {p['id']: p for p in res_p.data}
                preguntas_ordenadas = [preguntas_dict[pid] for pid in examen['preguntas_ids']]
                
                # 3. Cargar en session_state y activar modo revisión
                st.session_state.preguntas_examen = preguntas_ordenadas
                st.session_state.respuestas_usuario = {int(k): v for k, v in examen['respuestas_usuario'].items()}
                st.session_state.examen_finalizado = False
                st.session_state.ver_revision = True
                st.session_state.indice_revision = 0
                st.session_state.sub_pantalla = "repaso_historial"
                st.rerun()