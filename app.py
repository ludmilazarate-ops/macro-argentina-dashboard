import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página web
st.set_page_config(
    page_title="Tablero Macroeconómico - Argentina", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Título Principal
st.title("📊 Monitor Macroeconómico Semanal")
st.subheader("Información clave para consultores")
st.divider()

# 2. Conexión a Google Sheets
# REEMPLAZA ESTO: Poné el ID de tu propio Google Sheet acá abajo
SHEET_ID = "1zksr6ipnnKgYQJR8_H1PLdyiglmCAAaBe29Xb-8zCoY"
SHEET_NAME = "Datos_Macro"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

@st.cache_data(ttl=300) # Guarda en caché por 5 minutos para que cargue instantáneo
def cargar_datos():
    try:
        df = pd.read_csv(URL)
        # Convertimos la fecha a formato correcto para ordenar
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    except Exception as e:
        st.error("Error al conectar con Google Sheets. Verificá el ID y los permisos.")
        return None

df_master = cargar_datos()

if df_master is not None:
    # 3. Barra Lateral - Filtros
    st.sidebar.header("Filtros de Análisis")
    
    # Lista de sectores ordenada por tu prioridad interna
    sectores_disponibles = [
        "Comercio minorista", "Comercio mayorista", "Gastronomía", 
        "Construcción", "Servicios", "Industria", "Automotriz"
    ]
    
    sector_seleccionado = st.sidebar.selectbox(
        "Seleccioná el Sector a analizar:", 
        sectores_disponibles
    )
    
    # Filtrar datos por el sector elegido
    df_sector = df_master[df_master['Sector'] == sector_seleccionado].sort_values(by='Fecha', ascending=False)

    if not df_sector.empty:
        # Obtenemos el registro más reciente (el último lunes cargado)
        ultimo_registro = df_sector.iloc[0]
        
        # 4. Sección de KPIs / Métricas destacadas
        st.header(f"🔎 Situación Actual: {sector_seleccionado}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label=f"Último Dato ({ultimo_registro['Indicador']})", 
                value=str(ultimo_registro['Valor'])
            )
        with col2:
            st.metric(
                label="Variación Mensual (MoM)", 
                value=str(ultimo_registro['Variacion_Mensual'])
            )
        with col3:
            st.metric(
                label="Variación Interanual (YoY)", 
                value=str(ultimo_registro['Variacion_Anual'])
            )
            
        st.divider()
        
        # 5. Sección de Gráficos y Comentarios
        col_izq, col_der = st.columns([2, 1]) # El gráfico ocupa el doble de espacio
        
        with col_izq:
            st.subheader("📈 Evolución Histórica del Indicador")
            # Ordenamos cronológicamente para el gráfico
            df_grafico = df_sector.sort_values(by='Fecha')
            
            fig = px.line(
                df_grafico, 
                x='Fecha', 
                y='Valor', 
                title=f"Tendencia de: {ultimo_registro['Indicador']}",
                markers=True
            )
            fig.update_layout(xaxis_title="Fecha", yaxis_title="Valor / Índice")
            st.plotly_chart(fig, use_container_width=True)
            
        with col_der:
            st.subheader("📰 Claves de la Semana")
            # Mostramos el comentario que escribiste en el Sheet
            st.info(f"**Nota del analista:**\n\n{ultimo_registro['Comentario']}")
            
            # Un recordatorio útil para las reuniones de los consultores
            with st.expander("📌 Tips para la reunión"):
                st.write("""
                - Revisá la tendencia del gráfico antes de proponer estrategias.
                - Cruzá la variación interanual con las proyecciones de inflación.
                """)
    else:
        st.warning(f"No se encontraron datos cargados para el sector: {sector_seleccionado}. Asegurate de escribirlo bien en el Sheets.")

else:
    st.info("Esperando datos válidos para renderizar el tablero...")