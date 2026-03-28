import streamlit as st
import pandas as pd

def render_historial_screen(supabase):
    st.markdown('<div class="titulo-pantalla">📜 MI HISTORIAL</div>', unsafe_allow_html=True)
    
    # 1. Obtención de datos "en bruto"
    res = (
        supabase.table("historial_examenes")
        .select("*")
        .eq("user_id", st.session_state.user.id)
        .order("created_at", desc=True)
        .execute()
    )
    
    if not res.data:
        st.info("Aún no tienes exámenes en el historial.")
        return

    # Convertimos a DataFrame para que filtrar sea instantáneo y sencillo
    df_full = pd.DataFrame(res.data)
    
    # Filtro 1: Tipo de Examen
    tipo_filtro = st.segmented_control(
        "Tipo de Examen:",
        options=["Todos", "Temas", "Ingles", "Simulacro"],
        default="Todos",
        key="filtro_tipo"
    )

    # Filtro 2: Alcance / Estado
    alcance_filtro = st.segmented_control(
        "Ver:",
        options=["Últimos 10", "Todos", "Suspendidos"],
        default="Últimos 10",
        key="filtro_alcance"
    )

    # 3. APLICAR LÓGICA DE FILTRADO
    df_filtrado = df_full.copy()

    # Aplicar filtro de tipo
    if tipo_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo_examen'].str.upper() == tipo_filtro.upper()]

    # Aplicar filtro de alcance/estado
    if alcance_filtro == "Suspendidos":
        df_filtrado = df_filtrado[df_filtrado['nota_final'] < 5]
    elif alcance_filtro == "Últimos 10":
        df_filtrado = df_filtrado.head(10)

    st.write("---")

    # 4. RENDERIZADO DE TARJETAS (Usando el DF filtrado)
    if df_filtrado.empty:
        st.warning("No hay exámenes que coincidan con esos filtros.")
        return

    # Estilos CSS de las tarjetas (mantenemos tu diseño favorito)
    st.markdown("""
        <style>
        .card-historial {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 10px;
            border-left: 8px solid #4e4e4e;
        }
        </style>
    """, unsafe_allow_html=True)

    # Iteramos sobre el DataFrame filtrado
    for _, examen in df_filtrado.iterrows():
        nota = examen['nota_final']
        color_nota = "#2ecc71" if nota >= 5 else "#e74c3c"
        fecha = examen['created_at'][:10]
        
        st.markdown(f"""
            <div class="card-historial" style="border-left-color: {color_nota};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 0.75rem; opacity: 0.5;">{fecha}</span>
                        <h3 style="margin: 0; font-size: 1.1rem; color: white;">{examen['tipo_examen'].upper()}</h3>
                        <p style="margin: 2px 0 0 0; font-size: 0.85rem;">
                            {examen['aciertos']} ✅ | {examen['fallos']} ❌
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <b style="font-size: 1.7rem; color: {color_nota};">{nota:.1f}</b>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- BOTONES DE ACCIÓN (Dentro del bucle de exámenes) ---
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🔍 REPASAR", key=f"repaso_{examen['id']}", width='stretch'):
                with st.spinner("Cargando corrección..."):
                    # (Mantenemos tu lógica actual de carga para revisión)
                    res_p = supabase.table("preguntas").select("*").in_("id", examen['preguntas_ids']).execute()
                    preguntas_dict = {p['id']: p for p in res_p.data}
                    preguntas_ordenadas = [preguntas_dict[pid] for pid in examen['preguntas_ids']]
                    
                    st.session_state.preguntas_examen = preguntas_ordenadas
                    st.session_state.respuestas_usuario = {int(k): v for k, v in examen['respuestas_usuario'].items()}
                    st.session_state.ver_revision = True
                    st.session_state.indice_revision = 0
                    st.session_state.sub_pantalla = "repaso_historial"
                    st.rerun()

        with col_btn2:
            if st.button("🔄 REPETIR", key=f"repeat_{examen['id']}", width='stretch', type="primary"):
                with st.spinner("Preparando examen..."):
                    # 1. Recuperamos las mismas preguntas
                    res_p = supabase.table("preguntas").select("*").in_("id", examen['preguntas_ids']).execute()
                    preguntas_dict = {p['id']: p for p in res_p.data}
                    preguntas_ordenadas = [preguntas_dict[pid] for pid in examen['preguntas_ids']]
                    
                    # 2. CONFIGURACIÓN PARA EXAMEN NUEVO (Limpieza total)
                    st.session_state.preguntas_examen = preguntas_ordenadas
                    st.session_state.respuestas_usuario = {} # IMPORTANTE: Vacío para que no haya respuestas marcadas
                    st.session_state.indice_pregunta = 0
                    st.session_state.examen_finalizado = False
                    st.session_state.ver_revision = False
                    
                    # 3. Saltamos directamente al runtime del examen
                    # Usamos el tipo original para que cuando guarde, sepa qué categoría es
                    st.session_state.tipo_test_actual = examen['tipo_examen']
                    st.session_state.sub_pantalla = "examen_runtime" 
                    st.rerun()