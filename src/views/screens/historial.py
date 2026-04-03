import streamlit as st
import pandas as pd

def render_historial_screen(supabase):
    st.markdown('<div class="titulo-pantalla">📜 HISTORIAL</div>', unsafe_allow_html=True)
    
    # 1. Obtención de datos (Misma lógica funcional)
    res = (supabase.table("historial_examenes").select("*")
           .eq("user_id", st.session_state.user.id)
           .order("created_at", desc=True).execute())
    
    if not res.data:
        st.info("Sin historial.")
        return

    df_full = pd.DataFrame(res.data)
    
    # 2. Filtro Único (Se mantiene el comportamiento de los pills)
    filtro_sel = st.pills(
        "Filtrar:", ["Todos", "Suspensos"],
        default=st.session_state.get("f_filtro_unico", "Todos"),
        key="pills_hist_refact", label_visibility="collapsed"
    )

    if filtro_sel and filtro_sel != st.session_state.get("f_filtro_unico"):
        st.session_state.f_filtro_unico = filtro_sel
        st.rerun()

    df_filtrado = df_full.copy()
    if st.session_state.get("f_filtro_unico") == "Suspensos":
        df_filtrado = df_filtrado[df_filtrado['nota_final'] < 5]

    # 3. Renderizado de Tarjetas
    for _, examen in df_filtrado.iterrows():
        nota = examen['nota_final']
        riesgo = examen['nota_con_riesgo']
        color = "#2ecc71" if nota >= 5 else "#e74c3c"
        
        # HTML usando las nuevas clases del CSS
        st.markdown(f"""
            <div class="card-historial" style="border-left-color: {color};">
                <div class="card-header-flex">
                    <div style="line-height: 1.2;">
                        <span class="card-meta-fecha">{examen['created_at'][:10]}</span><br>
                        <span class="card-titulo-tipo">{examen['tipo_examen'].upper()}</span>
                        <div class="card-stats-iconos">{examen['aciertos']}✅ {examen['fallos']}❌ {examen['blancos']}⚪</div>
                    </div>
                    <div class="card-nota-grande" style="color: #fdfd96;">{riesgo:.1f}</div>
                    <div class="card-nota-grande" style="color: {color};">{nota:.1f}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- Botonera en una sola línea (Tu solución favorita) ---
        nav_container = st.container(horizontal=True)
        
        with nav_container:
            if st.button("🔍 REPASAR", key=f"rev_{examen['id']}", width='stretch'):
                _cargar_y_navegar(supabase, examen, modo_reintento=False)
                
            if st.button("🔄 REPETIR", key=f"rep_{examen['id']}", width='stretch', type="primary"):
                _cargar_y_navegar(supabase, examen, modo_reintento=True)
        
        st.write("") 

def _cargar_y_navegar(supabase, examen, modo_reintento):
    """Lógica interna refactorizada para evitar duplicidad."""
    with st.spinner("Cargando datos..."):
        res_p = supabase.table("preguntas").select("*").in_("id", examen['preguntas_ids']).execute()
        p_dict = {p['id']: p for p in res_p.data}
        
        # Seteo de variables comunes
        st.session_state.preguntas_examen = [p_dict[pid] for pid in examen['preguntas_ids']]
        st.session_state.preguntas_dudosas = examen['preguntas_dudosas']
        st.session_state.tipo_test_actual = examen['tipo_examen']
        st.session_state.indice_pregunta = 0
        st.session_state.indice_revision = 0
        st.session_state.examen_finalizado = False

        if modo_reintento:
            st.session_state.respuestas_usuario = {}
            st.session_state.ver_revision = False
            st.session_state.sub_pantalla = "examen_runtime"
        else:
            st.session_state.respuestas_usuario = {int(k): v for k, v in examen['respuestas_usuario'].items()}
            st.session_state.preguntas_dudosas = examen['preguntas_dudosas']
            st.session_state.ver_revision = True
            st.session_state.sub_pantalla = "repaso_historial"
        
        st.rerun()