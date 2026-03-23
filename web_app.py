import streamlit as st
from supabase import create_client
import random
import pandas as pd
import re
import pdfplumber
import plotly.express as px

def mostrar_progreso():
    st.markdown('<div class="titulo-pantalla">📊 MI PROGRESO</div>', unsafe_allow_html=True)
    # --- DATOS PARA GRÁFICO DE LÍNEAS (Evolución de Notas) ---
    res_h = supabase.table("historial_examenes")\
        .select("created_at, nota_final")\
        .eq("user_id", st.session_state.user.id)\
        .order("created_at")\
        .execute()
    
    # --- DATOS PARA GRÁFICO DE SECTORES (Fallos por Tema) ---
    # Traemos los errores y el nombre del tema haciendo un join sencillo
    res_e = supabase.table("errores_usuario")\
        .select("tema_id, temas(nombre)")\
        .eq("user_id", st.session_state.user.id)\
        .execute()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Nota media exámenes")
        if res_h.data:
            df_notas = pd.DataFrame(res_h.data)
            df_notas['Fecha'] = pd.to_datetime(df_notas['created_at']).dt.date
            # Agrupamos por fecha para obtener la media diaria
            df_media_dia = df_notas.groupby('Fecha')['nota_final'].mean().reset_index()
            df_media_dia['nota_final'] = df_media_dia['nota_final'].round(2)
            # CREACIÓN DEL GRÁFICO DE LÍNEAS
            fig_line = px.line(
                df_media_dia, 
                x='Fecha', 
                y='nota_final',
                markers=True, # Añade puntos en cada día
                text='nota_final', # Muestra la nota sobre el punto
                labels={'nota_final': 'Nota Media', 'Fecha': 'Día de Estudio'},
                template="plotly_dark" # Para que encaje con el modo oscuro
            )
            # Personalización de la línea y el área
            fig_line.update_traces(
                line_color='#00ffcc', # Un color neón que resalte
                line_width=3,
                marker=dict(size=10, symbol='circle', color='white', line=dict(width=2, color='#00ffcc')),
                textposition="top center"
            )
            # Ajustes de ejes y fondo
            fig_line.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(range=[0, 10.5], gridcolor='rgba(255,255,255,0.1)'), # Forzamos escala 0-10
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Aún no hay datos de exámenes.")

    with col2:
        st.subheader("🎯 Número de fallos por tema")
        if res_e.data:
            # Preparamos el DataFrame (Igual que antes)
            conteo_fallos = []
            for error in res_e.data:
                nombre_tema = error.get('temas', {}).get('nombre', 'Desconocido')
                conteo_fallos.append(nombre_tema)
            df_fallos = pd.DataFrame(conteo_fallos, columns=['Tema'])
            df_pie = df_fallos.value_counts().reset_index()
            df_pie.columns = ['Tema', 'Fallos']
            # CREACIÓN DEL GRÁFICO CON PLOTLY
            fig = px.pie(
                df_pie, 
                values='Fallos', 
                names='Tema', 
                hole=0.4, # Efecto Donut: queda más limpio y permite leer mejor
                color_discrete_sequence=px.colors.qualitative.T10 # Paleta de 10 colores distintos
            )
            # Ajustes de Estilo (Fondo transparente para que no desentone con tu CSS)
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="white"),
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
            )
            # Mostrar en Streamlit
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("¡Sin fallos registrados! Sigue así.")

    if st.button("⬅️ VOLVER AL MENÚ"):
        st.session_state.pantalla_actual = "principal"
        st.rerun()

def guardar_resultado_examen(datos_test, respuestas_usuario, tipo):
    """
    datos_test: Lista de diccionarios con las preguntas del test
    respuestas_usuario: Diccionario con {indice: 'A/B/C'}
    """
    aciertos = 0
    fallos = 0
    blancos = 0
    lista_errores = []

    for i, p in enumerate(datos_test):
        resp = respuestas_usuario.get(i)
        correcta = str(p['correcta']).upper().strip()
        
        if resp is None:
            blancos += 1
        elif resp == correcta:
            aciertos += 1
        else:
            fallos += 1
            # Preparamos el detalle del error para la tabla 'errores_usuario'
            lista_errores.append({
                "user_id": st.session_state.user.id,
                "tema_id": p.get('tema_id'),
                "pregunta_id": p.get('id')
                # El user_id y examen_id se añaden al insertar
            })

    # Fórmula de nota (ejemplo: aciertos - fallos/3 sobre 10)
    # Ajusta esta fórmula según la oposición real
    total = len(datos_test)
    nota = (aciertos - (fallos / 3)) * (10 / total) if total > 0 else 0
    nota = max(0, round(nota, 2)) # Que no baje de 0

    # 1. Insertar Resumen en 'historial_examenes'
    res_h = supabase.table("historial_examenes").insert({
        "user_id": st.session_state.user.id,
        "tipo_examen": tipo,
        "num_preguntas": total,
        "aciertos": aciertos,
        "fallos": fallos,
        "blancos": blancos,
        "nota_final": nota
    }).execute()

    # 2. Si hubo fallos, registrarlos vinculados al ID del examen recién creado
    if fallos > 0 and res_h.data:
        examen_id = res_h.data[0]['id']
        for error in lista_errores:
            error["examen_id"] = examen_id
        
        supabase.table("errores_usuario").insert(lista_errores).execute()
    
    return nota, aciertos, fallos
    
def convertir_a_csv(lista_preguntas):
    import io
    df_descarga = pd.DataFrame(lista_preguntas)
    df_descarga = df_descarga.rename(columns={
        "enunciado": "Enunciado",
        "opcion_a": "opcion_a",
        "opcion_b": "opcion_b",
        "opcion_c": "opcion_c",
        "correcta": "correcta",
        "explicacion": "Explicación"
    })
    return df_descarga.to_csv(index=False, sep=";").encode('utf-8')

def limpiar_ruido_general(texto):
    """Limpia cabeceras, pies y avisos de 'continúe' de todas las promociones"""
    patrones = [
        r'(?i)POLIC[ÍI]A\s+MUNICIPAL\s+MADRID',
        r'(?i)AYUNTAMIENTO\s+DE\s+MADRID',
        r'(?i)CUESTIONARIO\s+[A-Z]',
        r'(?i)P[ÁA]GINA\s+\d+',
        r'(?i)POL-B\s*-\s*\d+',
        r'(?i)Continúe\s+en\s+la\s+siguiente\s+página',
        r'(?i)Ha\s+finalizado\s+la\s+prueba',
        r'---\s+PAGE\s+\d+\s+---'
    ]
    for p in patrones:
        texto = re.sub(p, '', texto)
    return texto

def parsear_examen_universal(archivo_pdf):
    preguntas_extraidas = []
    texto_total = ""

    with pdfplumber.open(archivo_pdf) as pdf:
        for pagina in pdf.pages:
            raw = pagina.extract_text()
            if raw:
                texto_total += limpiar_ruido_general(raw) + "\n"

    # 1. Identificar el inicio de cada pregunta (Número + separador)
    # Buscamos patrones como: "1.-", "1.", "1) " al inicio de línea
    bloques = re.split(r'\n\s*(?=\d+[\.\-\)\s]+)', texto_total)

    for bloque in bloques:
        if not bloque.strip(): continue

        # 2. Extraer el enunciado: Todo lo que hay desde el inicio hasta la opción A
        # El regex busca A o a seguida de punto, paréntesis o guion
        match_enunciado = re.split(r'\n\s*(?=[aA][\.\-\)\s])', bloque, maxsplit=1)
        
        if len(match_enunciado) >= 2:
            enunciado_raw = match_enunciado[0]
            resto = match_enunciado[1]
            
            # Limpiar el número del enunciado (ej: "1.- ")
            enunciado = re.sub(r'^\d+[\.\-\)\s]+', '', enunciado_raw).strip()

            # 3. Extraer opciones B y C
            # Buscamos el separador de B y luego el de C
            match_b = re.split(r'\n\s*(?=[bB][\.\-\)\s])', resto, maxsplit=1)
            if len(match_b) >= 2:
                op_a = match_b[0].strip()
                match_c = re.split(r'\n\s*(?=[cC][\.\-\)\s])', match_b[1], maxsplit=1)
                
                if len(match_c) >= 2:
                    op_b = match_c[0].strip()
                    op_c = match_c[1].strip()
                    
                    # Limpiar letras sobrantes al inicio de las opciones si quedaran
                    op_a = re.sub(r'^[aA][\.\-\)\s]+', '', op_a).strip()
                    op_b = re.sub(r'^[bB][\.\-\)\s]+', '', op_b).strip()
                    op_c = re.sub(r'^[cC][\.\-\)\s]+', '', op_c).strip()

                    preguntas_extraidas.append({
                        "Enunciado": enunciado.replace('\n', ' '),
                        "opcion_a": op_a.replace('\n', ' '),
                        "opcion_b": op_b.replace('\n', ' '),
                        "opcion_c": op_c.replace('\n', ' '),
                        "correcta": "A",
                        "Explicación": "",
                        "Tema": ""
                    })

    return preguntas_extraidas
    
@st.dialog("Importar desde PDF")
def modal_importar_pdf():
    st.write("Sube el archivo PDF del examen. El sistema intentará extraer las preguntas y opciones automáticamente.")
    archivo = st.file_uploader("Seleccionar PDF", type=["pdf"], key="uploader_pdf_modal")
    
    if archivo:
        with st.spinner("Analizando estructura del examen..."):
            try:
                lista_preguntas = parsear_examen_universal(archivo)
                
                if lista_preguntas:
                    # Inyectamos los datos en la "mochila" de revisión
                    st.session_state.preguntas_pendientes = lista_preguntas
                    # Saltamos a la pantalla de revisión que ya creamos
                    st.session_state.sub_pantalla = "revision_importacion"
                    st.rerun()
                else:
                    st.error("No se detectaron preguntas. Asegúrate de que el PDF tenga el formato 1. Enunciado A. B. C.")
            except Exception as e:
                st.error(f"Error al procesar el PDF: {e}")
                
@st.dialog("Subir archivo de preguntas")
def modal_importar():
    st.write("Selecciona un archivo CSV con el formato correcto.")
    archivo = st.file_uploader("Arrastra tu archivo aquí", type=["csv"], key="uploader_modal")
    
    if archivo:
        try:
            df_temp = pd.read_csv(
                archivo, sep=";", encoding="utf-8", header=0, 
                names=['Enunciado', 'opcion_a', 'opcion_b', 'opcion_c', 'correcta', 'Explicación', 'Tema']
            ).fillna("")
            
            # Guardamos datos y cambiamos pantalla
            st.session_state.preguntas_pendientes = df_temp.to_dict('records')
            st.session_state.sub_pantalla = "revision_importacion"
            st.rerun() # Esto cierra el diálogo y salta de pantalla
        except Exception as e:
            st.error(f"Error: {e}")

def limpiar_estado_maestro():
    """
    Realiza un reseteo integral de la sesión. 
    Limpia variables de test, configuración, filtros e importación.
    """
    
    # 2. Definimos todas las variables que deben volver a su estado inicial
    # He incluido las de configuración de examen que detecté en tu lógica
    keys_a_limpiar = [
        "preguntas_examen",
        "respuestas",
        "tipo_test_actual",
        "nota_ultima",
        "preguntas",               # Lista de preguntas cargadas para el test
        "respuestas_usuario",      # Diccionario con lo que el usuario va marcando
        "test_finalizado",         # Estado de fin de examen
        "pregunta_actual",         # Índice del carrusel de preguntas
        "preguntas_pendientes",    # Datos temporales del PDF/CSV en revisión
        "temas_seleccionados",     # Filtro del multiselect de temas
        "num_preguntas_test",      # El número elegido en el slider/input
        "error_importacion",       # Posibles mensajes de error guardados
        "test_generado",           # Flag de control de generación
        "paso_configuracion"      # Reseteamos la pantalla en la que entramos al pulsar examen
    ]
    
    for key in keys_a_limpiar:
        if key in st.session_state:
            # Reseteo según el tipo de dato para evitar errores de tipo más adelante
            if key in ["preguntas_test", "preguntas", "preguntas_pendientes", "temas_seleccionados"]:
                st.session_state[key] = []
            elif key in ["respuestas_usuario","respuestas", "respuestas_usuario"]:
                st.session_state[key] = {}
            elif key in ["pregunta_actual", "num_preguntas_test"]:
                st.session_state[key] = 0
            elif key in ["test_finalizado", "test_generado"]:
                st.session_state[key] = False
            else:
                del st.session_state[key]

    # 3. Limpieza de fragmentos de UI (Widgets de archivo)
    # Esto ayuda a que el uploader no intente 're-subir' el mismo archivo al volver
    if "uploader_pdf_modal" in st.session_state:
        del st.session_state["uploader_pdf_modal"]
    if "uploader_modal" in st.session_state:
        del st.session_state["uploader_modal"]

def renderizar_formulario_edicion(p, nombres_temas, nombre_a_id):
    """Función auxiliar para encapsular el formulario de edición"""
    # Limpieza de nulos para evitar errores en widgets
    for key in list(p.keys()):
        if pd.isna(p[key]): p[key] = ""

    with st.container():
        # FILA 1: Enunciado y Explicación
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<p class="label-admin">ENUNCIADO DE LA PREGUNTA:</p>', unsafe_allow_html=True)
            f_enun = st.text_area("##enun", value=str(p['enunciado']), height=150, label_visibility="collapsed", key=f"enun_{p['id']}")
        with col2:
            st.markdown('<p class="label-admin">EXPLICACIÓN / BASE LEGAL:</p>', unsafe_allow_html=True)
            f_exp = st.text_area("##exp", value=str(p.get('explicacion', '')), height=150, label_visibility="collapsed", key=f"exp_{p['id']}")

        st.write("###") 

        # FILA 2: Opciones y Configuración
        col_izq, col_der = st.columns(2)
        
        with col_izq:
            st.markdown('<p class="label-admin">OPCIONES DE RESPUESTA:</p>', unsafe_allow_html=True)
            # Definición de sub-columnas para etiquetas A, B, C
            for letra in ["a", "b", "c"]:
                c_lab, c_inp = st.columns([0.05, 0.95])
                c_lab.markdown(f'<p style="margin-top:10px; font-weight:bold;">{letra.upper()}:</p>', unsafe_allow_html=True)
                val_opcion = str(p[f'opcion_{letra}'])
                # Creamos variables dinámicas para retornar (f_a, f_b, f_c)
                if letra == "a": f_a = c_inp.text_input(f"L_{letra}", value=val_opcion, label_visibility="collapsed", key=f"in_{letra}_{p['id']}")
                if letra == "b": f_b = c_inp.text_input(f"L_{letra}", value=val_opcion, label_visibility="collapsed", key=f"in_{letra}_{p['id']}")
                if letra == "c": f_c = c_inp.text_input(f"L_{letra}", value=val_opcion, label_visibility="collapsed", key=f"in_{letra}_{p['id']}")

        with col_der:
            st.markdown('<p class="label-admin">CONFIGURACIÓN:</p>', unsafe_allow_html=True)
            
            # Correcta
            c_labCorr, c_inpCorr = st.columns([0.2, 0.8])
            c_labCorr.markdown('<p style="margin-top:10px; font-weight:bold;">Correcta:</p>', unsafe_allow_html=True)
            
            # Normalizamos el valor que viene de la DB a minúscula
            val_correcta_db = str(p.get('correcta', 'A')).upper().strip()
            opciones = ["A", "B", "C"]
            idx_corr = opciones.index(val_correcta_db) if val_correcta_db in opciones else 0
        
            f_corr = c_inpCorr.selectbox(
                "Corr", 
                opciones, 
                index=idx_corr,
                label_visibility="collapsed", 
                key=f"corr_{p['id']}"
            )
            
            # Tema
            c_labTema, c_inpTema = st.columns([0.2, 0.8])
            c_labTema.markdown('<p style="margin-top:10px; font-weight:bold;">Tema:</p>', unsafe_allow_html=True)
            tema_actual = p.get('tema_nombre', '')
            idx_tema = nombres_temas.index(tema_actual) if tema_actual in nombres_temas else 0
            f_tema_sel = c_inpTema.selectbox("TemaSel", nombres_temas, index=idx_tema, label_visibility="collapsed", key=f"tema_{p['id']}")

    return f_enun, f_exp, f_a, f_b, f_c, f_corr, f_tema_sel

def mostrar_examen(titulo, lista_preguntas):
    st.markdown(f'<div class="titulo-pantalla">{titulo}</div>', unsafe_allow_html=True)
    # 1. MODO REVISIÓN INDIVIDUAL (Pantalla Completa)
    if st.session_state.get("ver_revision", False):
        idx_rev = st.session_state.get("indice_revision", 0)
        p = lista_preguntas[idx_rev]
        resp_usuario = st.session_state.respuestas_usuario.get(idx_rev)
        es_correcta = resp_usuario == p['correcta']

        st.progress((idx_rev + 1) / len(lista_preguntas), text=f"Revisando Pregunta {idx_rev + 1} de {len(lista_preguntas)}")

        st.markdown(f"#### {p['enunciado']}")

        # --- SECCIÓN DE OPCIONES (Alineación Corregida) ---
        opciones = [("A", p['opcion_a']), ("B", p['opcion_b']), ("C", p['opcion_c'])]
        for letra, texto in opciones:
            base_style = "padding: 12px; border-radius: 10px; margin: 8px 0; border-left: 5px solid "
            if letra == p['correcta']:
                # OPCIÓN CORRECTA: Fondo verde y borde verde
                st.markdown(f"""<div style=" {base_style} #2ecc71; background-color: rgba(46, 204, 113, 0.15);"><b style="color: white;">{letra}) {texto}</b> 
                        <span style="color: #2ecc71; margin-left: 10px;">(Correcta)</span>
                    </div>
                """, unsafe_allow_html=True)
                
            elif letra == resp_usuario and not es_correcta:
                # OPCIÓN FALLADA: Fondo rojo y borde rojo
                st.markdown(f"""
                    <div style=" {base_style} #e74c3c; background-color: rgba(231, 76, 60, 0.15);">
                        <span style="color: white;">{letra}) {texto}</span> <span style="color: #e74c3c; margin-left: 10px;">(Tu elección)</span>
                    </div>
                """, unsafe_allow_html=True)
                
            else:
                # OPCIÓN NEUTRA: Sin fondo pero con el MISMO margen y borde transparente para alinear
                st.markdown(f"""
                    <div style=" {base_style} transparent; background-color: transparent;">
                        <span style="color: #bdc3c7;">{letra}) {texto}</span>
                    </div>
                """, unsafe_allow_html=True)

        # --- SECCIÓN DE EXPLICACIÓN (Corregida para evitar errores de renderizado) ---
        st.write("---")
        # 1. Recuperamos la explicación
        exp_raw = p.get('explicacion', '')
        # 2. Solo dibujamos el cuadro si realmente hay contenido
        # Comprobamos que no sea None, ni una cadena vacía, ni solo espacios
        if exp_raw and str(exp_raw).strip():
            explicacion_completa = f"""
            <div style="background-color: rgba(0, 150, 255, 0.1); 
                        padding: 20px; 
                        border-radius: 10px; 
                        border-left: 5px solid #0891B2;
                        margin-bottom: 20px;">
                <p style="margin-top:0; margin-bottom: 10px; font-weight: bold; color: #0891B2; font-size: 1.1rem;">
                    💡 EXPLICACIÓN
                </p>
                <div style="font-size: 1rem; line-height: 1.6; color: #e0e0e0;">
                    {exp_raw}
                </div>
            </div>
            """
            st.markdown(explicacion_completa, unsafe_allow_html=True)
        else:
            # Si no hay explicación, mostramos un mensaje discreto o nada
            st.caption("No hay explicación disponible para esta pregunta.")
        st.write("---")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if idx_rev > 0:
                if st.button("⬅️ ANTERIOR", key="rev_prev", use_container_width=True):
                    st.session_state.indice_revision -= 1
                    st.rerun()
        with c2:
            if st.button("VOLVER AL RESUMEN", use_container_width=True):
                st.session_state.ver_revision = False
                st.rerun()
        with c3:
            if idx_rev < len(lista_preguntas) - 1:
                if st.button("SIGUIENTE ➡️", key="rev_next", use_container_width=True):
                    st.session_state.indice_revision += 1
                    st.rerun()

    # 2. PANTALLA DE RESULTADOS (Resumen de Notas)
    elif st.session_state.examen_finalizado:
        total = len(lista_preguntas)
        aciertos = sum(1 for i, p in enumerate(lista_preguntas) if st.session_state.respuestas_usuario.get(i) == p['correcta'])
        fallos = sum(1 for i, p in enumerate(lista_preguntas) if st.session_state.respuestas_usuario.get(i) is not None and st.session_state.respuestas_usuario.get(i) != p['correcta'])
        sin_responder = total - (aciertos + fallos)

        netas = aciertos - (fallos * 0.33)
        nota_diez = (max(0, netas) / total) * 10 

        st.markdown('<h2 style="text-align: center;">📊 RESULTADOS DEL EXAMEN</h2>', unsafe_allow_html=True)
        st.write("###")

        # Fila 1: Métricas centradas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div style="text-align: center;"><p style="font-size: 1.5rem; margin-bottom:0;">🟢 Aciertos</p><h1 style="color: #2ecc71; margin-top:0;">{aciertos}</h1></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div style="text-align: center;"><p style="font-size: 1.5rem; margin-bottom:0;">🔴 Fallos</p><h1 style="color: #e74c3c; margin-top:0;">{fallos}</h1></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div style="text-align: center;"><p style="font-size: 1.5rem; margin-bottom:0;">⚪ En blanco</p><h1 style="color: #bdc3c7; margin-top:0;">{sin_responder}</h1></div>', unsafe_allow_html=True)

        st.write("---")

        # Fila 2: Tarjetas de Netas y Nota
        c_netas, c_nota = st.columns(2)
        with c_netas:
            st.markdown(f"""<div style="background-color: #6D28D9; padding: 25px; border-radius: 15px; text-align: center; border: 1px solid #4C1D95;">
                <p style="margin:0; font-size: 1.3rem; color: #EDE9FE; font-weight: bold;">PREGUNTAS NETAS</p>
                <h1 style="margin:0; color: white; font-size: 3.5rem;">{netas:.2f}</h1>
            </div>""", unsafe_allow_html=True)
        with c_nota:
            st.markdown(f"""<div style="background-color: #0891B2; padding: 25px; border-radius: 15px; text-align: center; border: 1px solid #164E63;">
                <p style="margin:0; font-size: 1.3rem; color: #CFFAFE; font-weight: bold;">NOTA SOBRE 10</p>
                <h1 style="margin:0; color: white; font-size: 3.5rem;">{nota_diez:.2f}</h1>
            </div>""", unsafe_allow_html=True)

        st.write("###")
        col_rev, col_fin = st.columns(2)
        with col_rev:
            if st.button("🔍 REVISAR PREGUNTA A PREGUNTA", use_container_width=True):
                st.session_state.ver_revision = True
                st.session_state.indice_revision = 0
                st.rerun()
        with col_fin:
            if st.button("🏁 FINALIZAR Y VOLVER", use_container_width=True, type="primary"):
                st.session_state.ver_revision = False
                limpiar_estado_maestro()
                st.session_state.sub_pantalla = "seleccion_tema"
                st.rerun()

    # 3. INTERFAZ DEL TEST (En curso)
    else:
        idx = st.session_state.indice_pregunta
        p_actual = lista_preguntas[idx]

        st.progress((idx + 1) / len(lista_preguntas), text=f"Pregunta {idx + 1} de {len(lista_preguntas)}")
        st.markdown(f"#### {p_actual['enunciado']}")
        
        opciones_letras = ["A", "B", "C"]
        respuesta_guardada = st.session_state.respuestas_usuario.get(idx)
        indice_a_mostrar = opciones_letras.index(respuesta_guardada) if respuesta_guardada in opciones_letras else None

        opciones_texto = {"A": p_actual['opcion_a'], "B": p_actual['opcion_b'], "C": p_actual['opcion_c']}

        seleccion = st.radio(
            "Selecciona tu respuesta:",
            options=opciones_letras,
            format_func=lambda x: f"{x}) {opciones_texto[x]}",
            index=indice_a_mostrar,
            key=f"radio_preg_{idx}"
        )

        if seleccion:
            st.session_state.respuestas_usuario[idx] = seleccion

        st.write("---")
        col1, col2 = st.columns(2)
        with col1:
            if idx > 0:
                if st.button("⬅️ ANTERIOR", use_container_width=True):
                    st.session_state.indice_pregunta -= 1
                    st.rerun()
        with col2:
            if idx < len(lista_preguntas) - 1:
                if st.button("SIGUIENTE ➡️", use_container_width=True):
                    st.session_state.indice_pregunta += 1
                    st.rerun()
            else:
                if st.button("🏁 FINALIZAR Y GUARDAR", use_container_width=True):
                    nota, ok, ko = guardar_resultado_examen(
                        st.session_state.preguntas_examen, 
                        st.session_state.respuestas_usuario,
                        tipo=st.session_state.get('tipo_test_actual', 'Personalizado')
                    )
                    
                    st.session_state.examen_finalizado = True
                    st.rerun()

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="OpoPMM - Tu Plaza es Nuestra",
    layout="wide",
    initial_sidebar_state="auto"
)

# --- 2. CONEXIÓN A SUPABASE ---
# Asegúrate de tener estos nombres exactos en tus Secrets de Streamlit
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_SERVICE_KEY"]
supabase = create_client(url, key)

# --- 3. CARGA DE CSS ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- 4. INICIALIZACIÓN DE ESTADOS (SESSION STATE) ---
if "sub_pantalla" not in st.session_state:
    st.session_state.sub_pantalla = "inicio"
if "user" not in st.session_state:
    st.session_state.user = None
if "user_role" not in st.session_state:
    st.session_state.user_role = "invitado"
if "temas_seleccionados" not in st.session_state:
    st.session_state.temas_seleccionados = []
if "examen_iniciado" not in st.session_state:
    st.session_state.examen_iniciado = "NO"
if "preguntas_examen" not in st.session_state:
    st.session_state.preguntas_examen = []
if "indice_pregunta" not in st.session_state:
    st.session_state.indice_pregunta = 0
if "respuestas_usuario" not in st.session_state:
    st.session_state.respuestas_usuario = {}
if "examen_finalizado" not in st.session_state:
    st.session_state.examen_finalizado = False
if "configurando_examen" not in st.session_state:
    st.session_state.configurando_examen = False
if "modo_seleccionado" not in st.session_state:
    st.session_state.modo_seleccionado = None
if "paso_configuracion" not in st.session_state:
    st.session_state.paso_configuracion = "botones"
if "preguntas_pendientes" not in st.session_state:
    st.session_state.preguntas_pendientes = [] # Aquí irán las preguntas del CSV
if "mostrando_revision" not in st.session_state:
    st.session_state.mostrando_revision = False

def cambiar_vista(sub):
    st.session_state.sub_pantalla = sub
    st.session_state.p_seleccionada = None

def navegar_a(sub):
    limpiar_estado_maestro()
    cambiar_vista(sub)
    st.rerun()


# --- 5. LÓGICA DE NAVEGACIÓN LATERAL (SIDEBAR) ---
# Solo mostramos el sidebar si el usuario está logueado
if st.session_state.user:
    with st.sidebar:
        # Intentamos sacar el nombre del perfil
        try:
            res_p = supabase.table("profiles").select("nombre").eq("id", st.session_state.user.id).single().execute()
            nombre_db = res_p.data.get("nombre")
        except:
            nombre_db = None

        st.markdown('<p class="titulo-pantalla" style="font-size: 28px; text-align: left;">OpoPMM 🏆</p>', unsafe_allow_html=True)
        
        # Lógica de saludo: Si hay nombre lo pone, si no, solo Hola
        saludo = f"¡Hola, **{nombre_db}**!" if nombre_db else "¡Hola!"
        st.write(saludo)
        st.divider()
        if st.button("📊 PROGRESO", use_container_width=True):navegar_a("stats")
        if st.button("👤 MI PERFIL", use_container_width=True):navegar_a("perfil")
        if st.button("📚 BIBLIOTECA DE LEYES", use_container_width=True):navegar_a("biblioteca")
        if st.button("📝 REALIZAR TEST", use_container_width=True):navegar_a("seleccion_tema")
        # 5. Gestión Preguntas (Solo ADMIN)
        if st.session_state.user_role == "admin":
            st.write("")
            st.markdown('<p style="font-size: 11px; opacity: 0.6; margin-left: 5px; letter-spacing: 1px;">ADMINISTRACIÓN</p>', unsafe_allow_html=True)
            if st.button("⚙️ GESTIÓN PREGUNTAS", use_container_width=True):navegar_a("admin_preguntas")
        # 6. Cerrar Sesión (al final)
        st.write("###")
        if st.button("🚪 CERRAR SESIÓN", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.clear()
            st.rerun()

# --- 6. PANTALLAS PRINCIPALES ---

# --- PANTALLA: INICIO (PÚBLICA) ---
if st.session_state.sub_pantalla == "inicio":
    st.markdown(f'<div class="titulo-pantalla">OpoPMM</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("---")
        if st.button("¡VAMOS A POR LA PLAZA!", use_container_width=True, type="primary"):
            cambiar_vista("login")
            st.rerun()

# --- PANTALLA: LOGIN / REGISTRO ---
elif st.session_state.sub_pantalla == "login":
    st.markdown(f'<div class="titulo-pantalla">ACCESO</div>', unsafe_allow_html=True)
    tabs = st.tabs(["Entrar", "Registrarse"])
    
    with tabs[0]:
        email = st.text_input("Email", key="login_email")
        pw = st.text_input("Contraseña", type="password", key="login_pw")
        if st.button("INICIAR SESIÓN", use_container_width=True, type="primary"):
            try:
                # 1. Intentamos el login
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                
                # Verificamos que tenemos usuario antes de seguir
                if res.user:
                    st.session_state.user = res.user
                    
                    # 2. Consultar rol - Usamos el ID directamente del objeto 'res.user'
                    # Añadimos un pequeño manejo de error específico para el perfil
                    try:
                        p = supabase.table("profiles").select("role").eq("id", res.user.id).single().execute()
                        st.session_state.user_role = p.data['role'] if p.data else "regular"
                    except Exception as e:
                        # Si falla el perfil pero el login es ok, asignamos rol por defecto
                        st.session_state.user_role = "regular"
                    
                    # 3. CAMBIO DE VISTA Y REFRESCO
                    cambiar_vista("menu_principal")
                    st.rerun()
                else:
                    st.error("No se pudo recuperar la información del usuario.")
                    
            except Exception as e:
                # Capturamos el error real para no confundir al usuario
                # Si el error es de Supabase por credenciales, saldrá aquí
                st.error("Error de acceso: Revisa tus credenciales.")

    with tabs[1]:
        n_email = st.text_input("Nuevo Email", key="reg_email")
        n_pw = st.text_input("Nueva Contraseña", type="password", key="reg_pw")
        if st.button("CREAR CUENTA", use_container_width=True):
            try:
                # Si tienes la confirmación desactivada en Supabase, entra directo
                res = supabase.auth.sign_up({"email": n_email, "password": n_pw})
                st.success("¡Cuenta creada! Intenta loguearte ahora.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- PANTALLA: MENÚ PRINCIPAL (RESUMEN) ---
elif st.session_state.sub_pantalla == "menu_principal":
    st.markdown(f'<div class="titulo-pantalla">CENTRO DE CONTROL</div>', unsafe_allow_html=True)
    st.info("Bienvenido. Utiliza el menú de la izquierda para navegar por la aplicación.")
    
    # Dashboard rápido
    c1, c2, c3 = st.columns(3)
    c1.metric("Nota Media", "7.2", "0.5")
    c2.metric("Test Completados", "24")
    c3.metric("Días para Examen", "124")

# --- PANTALLA: ESTADÍSTICAS ---
elif st.session_state.sub_pantalla == "stats":
    mostrar_progreso()

# --- PANTALLA: PERFIL ---
elif st.session_state.sub_pantalla == "perfil":
    st.markdown(f'<div class="titulo-pantalla">MI PERFIL</div>', unsafe_allow_html=True)
    
    # 1. Recuperar datos actuales del perfil
    res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).single().execute()
    datos_perfil = res.data if res.data else {}

    # 2. Formulario de Datos Personales
    with st.container():
        st.write("### 📝 Datos Personales")
        
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
        
        # 3. Botón Guardar
        if st.button("💾 GUARDAR CAMBIOS", use_container_width=True, type="primary"):
            try:
                actualizacion = {
                    "nombre": nombre,
                    "apellidos": apellidos,
                    "telefono": telefono,
                    "direccion": direccion,
                    "ciudad": ciudad
                }
                
                supabase.table("profiles").update(actualizacion).eq("id", st.session_state.user.id).execute()
                st.success("¡Perfil actualizado correctamente!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- PANTALLA: BIBLIOTECA ---
elif st.session_state.sub_pantalla == "biblioteca":
    st.markdown('<div class="titulo-pantalla">📚 BIBLIOTECA LEGISLATIVA</div>', unsafe_allow_html=True)
    
    # 1. CARGA DE DATOS DESDE SUPABASE
    try:
        res = supabase.table("biblioteca").select("*").order("orden").execute()
        df_biblio = pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        df_biblio = pd.DataFrame() # Creamos uno vacío para que no rompa el código

    # --- PASO CRÍTICO: Inicialización de df_mostrar ---
    # Esto evita el NameError. Por defecto, mostrar es igual a lo que hay en la DB.
    df_mostrar = df_biblio.copy()

    # 2. BUSCADOR EN TIEMPO REAL
    st.write("### 🔍 Buscar Normativa")
    busqueda = st.text_input(
        "Introduce el nombre de la ley...", 
        placeholder="Ej: Constitución, Contratos, Procedimiento...", 
        label_visibility="collapsed",
        key="input_buscador_biblio"
    )

    # Filtrado dinámico
    if busqueda and not df_biblio.empty:
        df_mostrar = df_biblio[df_biblio['name'].str.contains(busqueda, case=False, na=False)]

    # 3. INTERFAZ DE COLUMNAS (65% Tabla, 35% Gestión)
    col_tabla, col_gestion = st.columns([0.65, 0.35])

    with col_tabla:
        if not df_mostrar.empty:
            event_biblio = st.dataframe(
                df_mostrar,
                column_order=("orden", "name"),
                column_config={
                    "orden": st.column_config.NumberColumn("Nº"),
                    "name": st.column_config.TextColumn("LEY / NORMA", width="900"),
                },
                hide_index=True,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key="tabla_biblioteca"
            )
            
            # Capturamos la fila seleccionada
            seleccion_indices = event_biblio.selection.rows
        else:
            st.info("No se han encontrado leyes que coincidan con tu búsqueda.")
            seleccion_indices = []

    with col_gestion:
        # --- LÓGICA DE GESTIÓN SEGÚN ROL ---
        if st.session_state.user_role == "admin":
            # EL ADMIN VE PESTAÑAS
            tab_ver, tab_nuevo = st.tabs(["🔍 Ver Ley", "➕ Añadir Nueva"])
            
            with tab_ver:
                if seleccion_indices:
                    # Obtenemos la ley seleccionada usando el índice del dataframe filtrado
                    ley_sel = df_mostrar.iloc[seleccion_indices[0]]
                    st.success(f"**Seleccionada:**\n{ley_sel['name']}")
                    
                    if ley_sel['url_pdf']:
                        st.link_button("📥 DESCARGAR / VER PDF", ley_sel['url_pdf'], use_container_width=True)
                    else:
                        st.warning("No hay URL configurada.")
                    
                    st.divider()
                    if st.button("🗑️ ELIMINAR REGISTRO", use_container_width=True, type="secondary"):
                        supabase.table("biblioteca").delete().eq("id", ley_sel['id']).execute()
                        st.success("Registro eliminado.")
                        st.rerun()
                else:
                    st.write("Selecciona una fila para gestionar.")

            with tab_nuevo:
                st.write("### Nuevo Registro")
                with st.form("form_nueva_ley_biblio", clear_on_submit=True):
                    nuevo_nombre = st.text_input("Nombre de la Ley")
                    nueva_url = st.text_input("URL del PDF (Enlace directo)")
                    siguiente_orden = int(df_biblio['orden'].max() + 1) if not df_biblio.empty else 1
                    nuevo_orden = st.number_input("Orden", value=siguiente_orden)
                    
                    if st.form_submit_button("AÑADIR A BIBLIOTECA", use_container_width=True):
                        if nuevo_nombre:
                            nueva_data = {"name": nuevo_nombre, "url_pdf": nueva_url, "orden": nuevo_orden}
                            supabase.table("biblioteca").insert(nueva_data).execute()
                            st.rerun()
                        else:
                            st.error("El nombre es obligatorio.")

        else:
            # EL USUARIO REGULAR NO VE PESTAÑAS, SOLO EL DETALLE
            st.markdown("### 📄 Detalles")
            if seleccion_indices:
                ley_sel = df_mostrar.iloc[seleccion_indices[0]]
                st.info(f"**Normativa:**\n{ley_sel['name']}")
                if ley_sel['url_pdf']:
                    st.link_button("📥 DESCARGAR / VER PDF", ley_sel['url_pdf'], use_container_width=True)
                else:
                    st.warning("Documento no disponible.")
            else:
                st.write("Selecciona una ley de la lista para ver el enlace de descarga.")

    st.write("---")
    if st.button("⬅️ VOLVER AL MENÚ", key="btn_volver_biblio"):
        limpiar_estado_maestro()
        cambiar_vista("menu_principal")
        st.rerun()
        
# --- PANTALLA: SELECCIÓN DE TEMA (EXÁMENES) ---
elif st.session_state.sub_pantalla == "seleccion_tema":
    # --- PASO 1: LOS 3 BOTONES PRINCIPALES ---
    if st.session_state.paso_configuracion == "botones":
        st.markdown(f'<div class="titulo-pantalla">MODO EXAMEN</div>', unsafe_allow_html=True)
        st.markdown('<div class="contenedor-test">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🇬🇧\n\nEXAMEN DE INGLÉS", use_container_width=True):
                st.session_state.modo_seleccionado = "ingles"
                st.session_state.paso_configuracion = "seleccion_cantidad"
                st.rerun()
        with col2:
            if st.button("📚\n\nEXAMEN POR TEMAS", use_container_width=True):
                st.session_state.modo_seleccionado = "por_temas"
                st.session_state.paso_configuracion = "seleccion_temas" # Va a la lista de temas
                st.rerun()
        with col3:
            if st.button("⏱️\n\nSIMULACRO EXAMEN", use_container_width=True):
                st.session_state.modo_seleccionado = "simulacro"
                st.session_state.paso_configuracion = "seleccion_cantidad"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- PASO 2: SELECCIÓN DE TEMAS (Solo para "Por Temas") ---
    elif st.session_state.paso_configuracion == "seleccion_temas":
        st.markdown(f'<div class="titulo-pantalla">SELECCION DE TEMAS</div>', unsafe_allow_html=True)
        try:
            # Consultamos la tabla temas para listar los temas
            res = supabase.table("temas").select("id, nombre").order("id").neq("id",1).execute()
            temas_db = res.data
            
            # Filtramos el ID 1 (Inglés) para que no salga en "Por Temas"
            opciones = {f"Tema {t['nombre']}": t['id'] for t in temas_db if t['id'] != 1}
            
            seleccion = st.multiselect("Selecciona una o varias leyes:", options=list(opciones.keys()))
            
            st.write("---")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("⬅️ VOLVER", use_container_width=True):
                    st.session_state.paso_configuracion = "botones"
                    st.rerun()
            with c2:
                if st.button("CONTINUAR ➡️", type="primary", use_container_width=True, disabled=not seleccion):
                    # Guardamos los IDs de los temas elegidos
                    st.session_state.temas_seleccionados = [opciones[s] for s in seleccion]
                    st.session_state.paso_configuracion = "seleccion_cantidad"
                    st.rerun()
        except Exception as e:
            st.error(f"Error cargando temas: {e}")

    # --- PASO 3: SELECCIÓN DE CANTIDAD (Para todos) ---
    elif st.session_state.paso_configuracion == "seleccion_cantidad":
        st.markdown(f'<div class="titulo-pantalla">NUMERO DE PREGUNTAS</div>', unsafe_allow_html=True)
        st.write(f"Modo: **{st.session_state.modo_seleccionado.upper()}**")
        
        cantidad = st.select_slider(
            "¿Cuántas preguntas quieres responder?",
            options=[10, 20, 40, 80, 100],
            value=20
        )
        
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⬅️ VOLVER", use_container_width=True):
                # Si venía de temas, vuelve a temas. Si no, a los botones.
                if st.session_state.modo_seleccionado == "por_temas":
                    st.session_state.paso_configuracion = "seleccion_temas"
                else:
                    st.session_state.paso_configuracion = "botones"
                st.rerun()
        with c2:
            if st.button("🚀 EMPEZAR EXAMEN", type="primary", use_container_width=True):
                st.session_state.cantidad_preguntas = cantidad
                st.session_state.sub_pantalla = f"test_{st.session_state.modo_seleccionado}"
                st.rerun()

# --- MODO 1: INGLÉS ---
elif st.session_state.sub_pantalla == "test_ingles":
    if not st.session_state.preguntas_examen:
        limite_elegido = st.session_state.get("cantidad_preguntas", 20)
        st.session_state.tipo_test_actual = "ingles"
        try:
            # Traemos TODAS las de inglés
            res = supabase.table("preguntas").select("*").eq("tema_id", 1).execute()
            
            if res.data:
                todo_el_banco = res.data
                random.shuffle(todo_el_banco) # Barajamos todo el mazo primero
                st.session_state.preguntas_examen = todo_el_banco[:limite_elegido] # Cortamos
                
                st.session_state.indice_pregunta = 0
                st.session_state.respuestas_usuario = {}
                st.session_state.examen_finalizado = False
                st.rerun()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            if st.button("Volver al menú"):
                navegar_a("botones")
    
    # IMPORTANTE: Esto queda fuera del bloque 'if not st.session_state.preguntas_examen'
    if st.session_state.preguntas_examen:
        mostrar_examen("EXAMEN DE INGLÉS", st.session_state.preguntas_examen)

# --- MODO 2: POR TEMAS ---
elif st.session_state.sub_pantalla == "test_por_temas":
    if not st.session_state.preguntas_examen:
        ids_seleccionados = st.session_state.get("temas_seleccionados", [])
        limite_elegido = st.session_state.get("cantidad_preguntas", 20)
        st.session_state.tipo_test_actual = "temas"
        try:
            # Traemos todo lo que NO sea inglés (ID != 1)
            res = supabase.table("preguntas").select("*").in_("tema_id", ids_seleccionados).execute()
            if res.data:
                todo_el_banco = res.data
                random.shuffle(todo_el_banco)
                st.session_state.preguntas_examen = todo_el_banco[:limite_elegido]
                
                st.session_state.indice_pregunta = 0
                st.session_state.respuestas_usuario = {}
                st.session_state.examen_finalizado = False
                st.rerun()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            if st.button("Volver al menú"):
                navegar_a("botones")
    
    # IMPORTANTE: Esto queda fuera del bloque 'if not st.session_state.preguntas_examen'
    if st.session_state.preguntas_examen:
        mostrar_examen("EXAMEN POR TEMAS", st.session_state.preguntas_examen)

# --- MODO 3: SIMULACRO ---
elif st.session_state.sub_pantalla == "test_simulacro":
    if not st.session_state.preguntas_examen:
        limite_elegido = st.session_state.get("cantidad_preguntas", 20)
        st.session_state.tipo_test_actual = "simulacro"
        try:
            # Traemos todo lo que NO sea inglés (ID != 1)
            res = supabase.table("preguntas").select("*").neq("tema_id", 1).execute()
            
            if res.data:
                todo_el_banco = res.data
                random.shuffle(todo_el_banco)
                st.session_state.preguntas_examen = todo_el_banco[:limite_elegido]
                
                st.session_state.indice_pregunta = 0
                st.session_state.respuestas_usuario = {}
                st.session_state.examen_finalizado = False
                st.rerun()
        except Exception as e:
            st.error(f"Error al conectar con la base de datos: {e}")
            if st.button("Volver al menú"):
                navegar_a("botones")
    
    # IMPORTANTE: Esto queda fuera del bloque 'if not st.session_state.preguntas_examen'
    if st.session_state.preguntas_examen:
        mostrar_examen("SIMULACRO GENERAL", st.session_state.preguntas_examen)

# --- PANTALLA: GESTIÓN DE PREGUNTAS ---
elif st.session_state.sub_pantalla == "admin_preguntas":
    st.markdown('<div class="titulo-pantalla">PANEL DE GESTIÓN DE PREGUNTAS</div>', unsafe_allow_html=True)

    # 1. CARGA DE DATOS MAESTROS
    res_temas = supabase.table("temas").select("id, nombre").execute()
    id_a_nombre = {t['id']: t['nombre'] for t in res_temas.data}
    nombre_a_id = {t['nombre']: t['id'] for t in res_temas.data}
    nombres_temas = sorted(list(nombre_a_id.keys()))

    # 2. CSS DINÁMICO (Bordes iluminados para modo creación)
    if st.session_state.get("modo_creacion_pregunta", False):
        st.markdown("""
            <style>
                input, textarea, div[data-baseweb="select"] {
                    border: 2px solid #00F2FE !important;
                    box-shadow: 0 0 12px rgba(0, 242, 254, 0.6) !important;
                }
                @keyframes pulse-border {
                    0% { box-shadow: 0 0 5px rgba(0, 242, 254, 0.4); }
                    50% { box-shadow: 0 0 15px rgba(0, 242, 254, 0.8); }
                    100% { box-shadow: 0 0 5px rgba(0, 242, 254, 0.4); }
                }
                input, textarea { animation: pulse-border 2s infinite !important; }
            </style>
        """, unsafe_allow_html=True)

    # 3. TABLA DE PREGUNTAS EXISTENTES
    res_p = supabase.table("preguntas").select("*").order("id", desc=True).execute()
    if res_p.data:
        df_p = pd.DataFrame(res_p.data)
        df_p['tema_nombre'] = df_p['tema_id'].map(id_a_nombre).fillna("Sin Tema")
        
        st.write("### 📋 Banco de Preguntas")
        event = st.dataframe(
            df_p,
            column_order=("id", "enunciado", "tema_nombre"),
            column_config={
                "id": st.column_config.Column("ID", width=50),
                "enunciado": st.column_config.TextColumn("Enunciado", width=800),
                "tema_nombre": st.column_config.TextColumn("Tema", width="medium"),
            },
            hide_index=True, use_container_width=True, on_select="rerun", selection_mode="single-row",
            key="tabla_admin_preguntas"
        )

        if event.selection.rows:
            st.session_state.modo_creacion_pregunta = False
            st.session_state.p_seleccionada = df_p.iloc[event.selection.rows[0]].to_dict()

    # 4. FORMULARIO DE EDICIÓN / CREACIÓN
    st.divider()
    modo_crear = st.session_state.get("modo_creacion_pregunta", False)
    p_sel = st.session_state.get("p_seleccionada")

    if modo_crear:
        st.markdown('<h3 style="color: #00F2FE;">➕ CREANDO NUEVA PREGUNTA</h3>', unsafe_allow_html=True)
        p_init = {"id": None, "enunciado": "", "explicacion": "", "opcion_a": "", "opcion_b": "", "opcion_c": "", "correcta": "A", "tema_id": res_temas.data[0]['id'] if res_temas.data else None}
        f_vals = renderizar_formulario_edicion(p_init, nombres_temas, nombre_a_id)
    elif p_sel:
        st.markdown('<h3 style="color: #FFA500;">📝 EDITANDO PREGUNTA</h3>', unsafe_allow_html=True)
        f_vals = renderizar_formulario_edicion(p_sel, nombres_temas, nombre_a_id)
    else:
        st.info("💡 Selecciona una pregunta o pulsa 'NUEVA'.")
        f_vals = None

    # 5. BOTONERA INFERIOR
    st.write("###")
    b1, b2, b3, b4, b5 = st.columns(5)
    
    with b1:
        if st.button("➕ NUEVA", use_container_width=True, key="btn_nueva"):
            st.session_state.p_seleccionada = None
            st.session_state.modo_creacion_pregunta = True
            st.rerun()

    with b2:
        if st.button("📄 PDF A REVISIÓN", use_container_width=True, key="btn_pdf"):
            modal_importar_pdf()

    with b3:
        if st.button("📤 IMPORTAR", use_container_width=True, key="btn_import_trigger"):
            modal_importar()
    with b4:
        if f_vals:
            if st.button("💾 GUARDAR", type="primary", use_container_width=True):
                try:
                    # 1. Obtener ID del tema
                    nombre_tema_sel = f_vals[6]
                    id_tema_final = nombre_a_id.get(nombre_tema_sel)

                    if not id_tema_final:
                        st.error("❌ Tema no válido")
                    else:
                        # 2. Construir el objeto exactamente como pide la tabla 'preguntas'
                        upd = {
                            "enunciado": str(f_vals[0]).strip(),
                            "explicacion": str(f_vals[1]).strip(),
                            "opcion_a": str(f_vals[2]).strip(),
                            "opcion_b": str(f_vals[3]).strip(),
                            "opcion_c": str(f_vals[4]).strip(),
                            "correcta": str(f_vals[5]).upper().strip(), # AQUÍ está la clave del check constraint
                            "tema_id": id_tema_final
                        }

                        with st.spinner("Guardando..."):
                            if modo_crear:
                                supabase.table("preguntas").insert(upd).execute()
                                st.success("✅ Creada")
                            else:
                                supabase.table("preguntas").update(upd).eq("id", p_sel['id']).execute()
                                st.success("✅ Actualizada")
                            
                            st.session_state.modo_creacion_pregunta = False
                            st.session_state.p_seleccionada = None
                            st.rerun()
                except Exception as e:
                    st.error(f"Error técnico: {str(e)}")

    with b5:
        if p_sel and not modo_crear:
            if st.button("🗑️ ELIMINAR", use_container_width=True):
                supabase.table("preguntas").delete().eq("id", p_sel['id']).execute()
                st.session_state.p_seleccionada = None
                st.rerun()
        else:
            st.button("🗑️ ELIMINAR", use_container_width=True, disabled=True)

# --- PANTALLA INTERMEDIA: REVISIÓN DE IMPORTACIÓN ---
elif st.session_state.sub_pantalla == "revision_importacion":
    st.markdown('<div class="titulo-pantalla">🧐 REVISIÓN DE PREGUNTAS IMPORTADAS</div>', unsafe_allow_html=True)
    
    if not st.session_state.get("preguntas_pendientes"):
        st.warning("No quedan preguntas para revisar.")
        if st.button("⬅️ VOLVER AL PANEL"):
            limpiar_estado_maestro()
            st.session_state.sub_pantalla = "admin_preguntas"
            st.rerun()
        st.stop()

    # Carga de datos maestros para los selectores
    res_t = supabase.table("temas").select("id, nombre").execute()
    nombres_temas = sorted([t['nombre'] for t in res_t.data])
    nom_a_id = {t['nombre']: t['id'] for t in res_t.data}
    id_a_nom = {t['id']: t['nombre'] for t in res_t.data}

    st.info(f"Tienes **{len(st.session_state.preguntas_pendientes)}** preguntas pendientes de importar.")

    preguntas_para_subir = []
    
    # Usamos una copia de la lista para evitar errores al eliminar elementos durante el bucle
    for i, p in enumerate(st.session_state.preguntas_pendientes):
        with st.expander(f"Pregunta {i+1}: {str(p.get('Enunciado'))[:80]}...", expanded=(i == 0)):
            
            # --- FILA 1: CUERPO Y CONTROL ---
            col_izq, col_der = st.columns([2, 1])
            
            with col_izq:
                enun = st.text_area("Enunciado", value=p.get('Enunciado'), key=f"rev_enun_{i}", height=120)
                exp = st.text_area("Explicación / Base Legal", value=p.get('Explicación'), key=f"rev_exp_{i}", height=100)
            
            with col_der:
                if st.button(f"🗑️ ELIMINAR PREGUNTA {i+1}", key=f"btn_del_{i}", use_container_width=True):
                    st.session_state.preguntas_pendientes.pop(i)
                    st.rerun()
                
                tema_id_csv = p.get('Tema')
                try:
                    tema_id_val = int(tema_id_csv)
                    nombre_preasignado = id_a_nom.get(tema_id_val)
                except:
                    nombre_preasignado = None
                idx_t = nombres_temas.index(nombre_preasignado) if nombre_preasignado in nombres_temas else 0
                t_sel = st.selectbox("Asignar Tema", nombres_temas, index=idx_t, key=f"rev_tema_{i}")
                
                corr_csv = str(p.get('correcta', 'A')).strip().upper()
                idx_c = ["A", "B", "C"].index(corr_csv) if corr_csv in ["A", "B", "C"] else 0
                c_sel = st.selectbox("Opción Correcta", ["A", "B", "C"], index=idx_c, key=f"rev_corr_{i}")

            st.divider()

            # --- FILA 2: OPCIONES DE RESPUESTA ---
            st.write("**Opciones de respuesta:**")
            
            # Usamos columnas pequeñas para las etiquetas A, B, C y grandes para el texto
            # Así quedan alineadas verticalmente y ganamos ancho para el texto
            for letra, campo in zip(["A", "B", "C"], ["opcion_a", "opcion_b", "opcion_c"]):
                c_label, c_input = st.columns([0.1, 2.9])
                with c_label:
                    st.markdown(f"<p style=margin-top:10px; font-weight:bold;'>{letra}</p>", unsafe_allow_html=True)
                with c_input:
                    # Usamos text_input para que sea más limpio, o text_area si son muy largas
                    globals()[f"o{letra.lower()}"] = st.text_input(f"Contenido de la opción {letra}", value=p.get(campo), key=f"rev_{letra.lower()}_{i}",label_visibility="collapsed")
            # Guardamos los cambios realizados en el formulario
            preguntas_para_subir.append({
                "enunciado": enun, "opcion_a": oa, "opcion_b": ob, "opcion_c": oc,
                "correcta": c_sel.lower(), "explicacion": exp, "tema_id": nom_a_id[t_sel]
            })

# --- BOTONERA DE ACCIÓN GLOBAL ---
    st.divider()
    c_bot1, c_bot2, c_bot3 = st.columns(3) # Cambiamos a 3 columnas
    
    with c_bot1:
        if st.button("❌ CANCELAR TODO", use_container_width=True):
            st.session_state.preguntas_pendientes = []
            limpiar_estado_maestro()
            st.session_state.sub_pantalla = "admin_preguntas"
            st.rerun()

    with c_bot2:
        # Generamos el contenido del CSV con lo que hay AHORA en pantalla
        csv_data = convertir_a_csv(preguntas_para_subir)
        
        st.download_button(
            label="💾 GUARDAR PROGRESO (CSV)",
            data=csv_data,
            file_name="revision_parcial_examen.csv",
            mime="text/csv",
            use_container_width=True,
            help="Descarga lo que llevas hecho para seguir en otro momento"
        )
            
    with c_bot3:
        if st.button("🚀 SUBIR A BASE DE DATOS", type="primary", use_container_width=True):
            if preguntas_para_subir:
                with st.spinner("Guardando en Supabase..."):
                    supabase.table("preguntas").insert(preguntas_para_subir).execute()
                    st.success(f"¡{len(preguntas_para_subir)} preguntas añadidas!")
                    st.session_state.preguntas_pendientes = []
                    limpiar_estado_maestro()
                    st.session_state.sub_pantalla = "admin_preguntas"
                    st.rerun()

            st.session_state.paso_configuracion = "principal"
            st.rerun()
