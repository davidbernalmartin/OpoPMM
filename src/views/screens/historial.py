import streamlit as st
import pandas as pd

def render_historial_screen(supabase):
    st.markdown('<div class="titulo-pantalla">📜 MI HISTORIAL</div>', unsafe_allow_html=True)
    
    # 1. CSS Limpio y específico para las tarjetas
    st.markdown("""
        <style>
        .card-historial {
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 5px;
            border-left: 6px solid #4e4e4e;
        }
        /* Intentamos reducir el espacio entre botones para que quepan */
        .stButton button {
            padding: 5px 10px !important;
            height: auto !important;
            min-height: 35px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 2. Obtención y filtrado (Igual que antes, esto funciona bien)
    res = (supabase.table("historial_examenes").select("*")
           .eq("user_id", st.session_state.user.id)
           .order("created_at", desc=True).execute())
    
    if not res.data:
        st.info("Sin historial.")
        return

    df_full = pd.DataFrame(res.data)
    
    # Filtros
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        tipo_filtro = st.segmented_control("Tipo:", ["Todos", "Temas", "Ingles", "Simulacro"], default="Todos", key="f_tipo")
    with c_f2:
        alcance_filtro = st.segmented_control("Ver:", ["Últimos 10", "Todos", "Suspendidos"], default="Últimos 10", key="f_alcance")

    df_filtrado = df_full.copy()
    if tipo_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo_examen'].str.upper() == tipo_filtro.upper()]
    if alcance_filtro == "Suspendidos":
        df_filtrado = df_filtrado[df_filtrado['nota_final'] < 5]
    elif alcance_filtro == "Últimos 10":
        df_filtrado = df_filtrado.head(10)

    # 3. Renderizado de Tarjetas
    for _, examen in df_filtrado.iterrows():
        nota = examen['nota_final']
        color_nota = "#2ecc71" if nota >= 5 else "#e74c3c"
        
        # Tarjeta compacta en una sola línea de texto para ahorrar espacio
        st.markdown(f"""
            <div class="card-historial" style="border-left-color: {color_nota};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="line-height: 1.2;">
                        <span style="font-size: 0.7rem; opacity: 0.5;">{examen['created_at'][:10]}</span><br>
                        <b style="font-size: 0.95rem;">{examen['tipo_examen'].upper()}</b>
                        <div style="font-size: 0.8rem; opacity: 0.8;">{examen['aciertos']}✅ {examen['fallos']}❌</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.4rem; color: {color_nota}; font-weight: bold;">{nota:.1f}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- SOLUCIÓN PARA LOS BOTONES ---
        # Usamos columnas pero con un truco: Si fallan, el diseño sigue siendo limpio
        flex = st.container(horizontal=True)
        if flex.button("🔍 REPASAR", key=f"rev_{examen['id']}", use_container_width=True):
            # Lógica de carga...
            res_p = supabase.table("preguntas").select("*").in_("id", examen['preguntas_ids']).execute()
            p_dict = {p['id']: p for p in res_p.data}
            st.session_state.preguntas_examen = [p_dict[pid] for pid in examen['preguntas_ids']]
            st.session_state.respuestas_usuario = {int(k): v for k, v in examen['respuestas_usuario'].items()}
            st.session_state.ver_revision = True
            st.session_state.sub_pantalla = "repaso_historial"
            st.rerun()
        # El botón de repetir ahora es más corto "REPETIR" para que quepa mejor
        if flex.button("🔄 REPETIR", key=f"rep_{examen['id']}", use_container_width=True, type="primary"):
            # Lógica de reintento...
            res_p = supabase.table("preguntas").select("*").in_("id", examen['preguntas_ids']).execute()
            p_dict = {p['id']: p for p in res_p.data}
            st.session_state.preguntas_examen = [p_dict[pid] for pid in examen['preguntas_ids']]
            st.session_state.respuestas_usuario = {}
            st.session_state.indice_pregunta = 0
            st.session_state.examen_finalizado = False
            st.session_state.ver_revision = False
            st.session_state.tipo_test_actual = examen['tipo_examen']
            st.session_state.sub_pantalla = "examen_runtime"
            st.rerun()
        
        st.write("") # Separador sutil