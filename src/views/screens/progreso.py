"""Progress/statistics screen renderer."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


def render_progreso_screen(*, supabase: Any, user_id: str) -> None:
    st.markdown('<div class="titulo-pantalla">📊 MI PROGRESO</div>', unsafe_allow_html=True)
    res_h = (
        supabase.table("historial_examenes")
        .select("created_at, nota_final")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )

    res_e = supabase.table("errores_usuario").select("tema_id, temas(nombre)").eq("user_id", user_id).execute()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Nota media exámenes")
        if res_h.data:
            df_notas = pd.DataFrame(res_h.data)
            df_notas["Fecha"] = pd.to_datetime(df_notas["created_at"]).dt.date
            df_media_dia = df_notas.groupby("Fecha")["nota_final"].mean().reset_index()
            df_media_dia["nota_final"] = df_media_dia["nota_final"].round(2)
            fig_line = px.line(
                df_media_dia,
                x="Fecha",
                y="nota_final",
                markers=True,
                text="nota_final",
                labels={"nota_final": "Nota Media", "Fecha": "Día de Estudio"},
                template="plotly_dark",
            )
            fig_line.update_traces(
                line_color="#00ffcc",
                line_width=3,
                marker=dict(size=10, symbol="circle", color="white", line=dict(width=2, color="#00ffcc")),
                textposition="top center",
            )
            fig_line.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0, 10.5], gridcolor="rgba(255,255,255,0.1)"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig_line, width='stretch')
        else:
            st.info("Aún no hay datos de exámenes.")

    with col2:
        st.subheader("🎯 Número de fallos por tema")
        if res_e.data:
            conteo_fallos = []
            for error in res_e.data:
                nombre_tema = error.get("temas", {}).get("nombre", "Desconocido")
                conteo_fallos.append(nombre_tema)
            df_fallos = pd.DataFrame(conteo_fallos, columns=["Tema"])
            df_pie = df_fallos.value_counts().reset_index()
            df_pie.columns = ["Tema", "Fallos"]
            fig = px.pie(
                df_pie,
                values="Fallos",
                names="Tema",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.T10,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("¡Sin fallos registrados! Sigue así.")
