import streamlit as st
import pandas as pd

def render_historial_screen(supabase):
    st.markdown('<div class="titulo-pantalla">📜 HISTORIAL</div>', unsafe_allow_html=True)
    
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
    
    # --- SECCIÓN DE FILTRO ÚNICO ---

    # Inicializamos el estado si no existe
    if "f_filtro_unico" not in st.session_state:
        st.session_state.f_filtro_unico = "Todos"

    # Renderizamos los pills (ocupan muy poco espacio)
    filtro_seleccionado = st.pills(
        "Filtrar por resultado:",
        options=["Todos", "Suspensos"],
        default=st.session_state.f_filtro_unico,
        key="pills_unico_historial",
        label_visibility="collapsed" # Ocultamos el texto para que sea más limpio
    )

    # Si el usuario cambia la opción, guardamos y recargamos
    if filtro_seleccionado and filtro_seleccionado != st.session_state.f_filtro_unico:
        st.session_state.f_filtro_unico = filtro_seleccionado
        st.rerun()

    # --- LÓGICA DE FILTRADO SIMPLIFICADA ---

    df_filtrado = df_full.copy()

    # Aplicamos el filtro según la selección
    if st.session_state.f_filtro_unico == "Suspensos":
        # Filtramos por nota menor a 5
        df_filtrado = df_filtrado[df_filtrado['nota_final'] < 5]

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
            st.session_state.indice_revision = 0
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