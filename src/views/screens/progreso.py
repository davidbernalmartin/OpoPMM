"""Progress/statistics screen renderer."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


def render_progreso_screen(*, supabase: Any, user_id: str) -> None:
    st.markdown('<div class="titulo-pantalla">📊 MI PROGRESO</div>', unsafe_allow_html=True)
    
    # 1. Obtención de datos
    res_h = (
        supabase.table("historial_examenes")
        .select("created_at, nota_final")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    res_e = supabase.table("errores_usuario").select("tema_id, temas(nombre)").eq("user_id", user_id).execute()

    # 2. KPIs Superiores
    if res_h.data:
        df_notas = pd.DataFrame(res_h.data)
        nota_media = df_notas["nota_final"].mean()
        total_tests = len(df_notas)
        
    with st.container(horizontal=True):
        # Tarjeta de Nota Media
        st.markdown(f"""
            <div style="background: rgba(0, 255, 204, 0.1); border: 1px solid #00ffcc; 
                        padding: 15px; border-radius: 15px; text-align: center;">
                <span style="font-size: 0.8rem; color: #00ffcc; font-weight: bold;">NOTA MEDIA</span><br>
                <b style="font-size: 1.8rem;">{nota_media:.2f}</b>
            </div>
        """, unsafe_allow_html=True, width="stretch")

        # Tarjeta de Tests Hechos
        st.markdown(f"""
            <div style="background: rgba(109, 40, 217, 0.1); border: 1px solid #6D28D9; 
                        padding: 15px; border-radius: 15px; text-align: center;">
                <span style="font-size: 0.8rem; color: #6D28D9; font-weight: bold;">TESTS</span><br>
                <b style="font-size: 1.8rem;">{total_tests}</b>
            </div>
        """, unsafe_allow_html=True, width="stretch")

    # 3. Gráficos con width="stretch"
    st.markdown("#### 📈 Evolución de Notas")
    if res_h.data:
        df_notas["Fecha"] = pd.to_datetime(df_notas["created_at"]).dt.date
        df_media_dia = df_notas.groupby("Fecha")["nota_final"].mean().reset_index()
        
        fig_line = px.line(
            df_media_dia,
            x="Fecha",
            y="nota_final",
            markers=True,
            template="plotly_dark",
        )
        fig_line.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10),
        )
        # Cambio aplicado: width='stretch'
        st.plotly_chart(fig_line, width="stretch", config={'displayModeBar': False})
    
    st.write("---")

    st.markdown("#### 🎯 Fallos por Tema")
    if res_e.data:
        conteo_fallos = [error.get("temas", {}).get("nombre", "Desconocido") for error in res_e.data]
        df_pie = pd.DataFrame(conteo_fallos, columns=["Tema"]).value_counts().reset_index()
        df_pie.columns = ["Tema", "Fallos"]
        
        fig_pie = px.pie(df_pie, values="Fallos", names="Tema", hole=0.5)
        fig_pie.update_layout(
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=-0.2),
        )
        # Cambio aplicado: width='stretch'
        st.plotly_chart(fig_pie, width="stretch", config={'displayModeBar': False})