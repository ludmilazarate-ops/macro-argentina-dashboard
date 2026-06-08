import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests

# 1. Configuración de la aplicación web
st.set_page_config(
    page_title="Lunes Macro - Consultores", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos estéticos para semáforos y solapas
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        background-color: #f0f2f6;
        border-radius: 5px;
    }
    .stTabs [aria-selected="true"] { background-color: #0083B0 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)


# --- CONEXIÓN AUTOMÁTICA A API DE DÓLARES (Mercado en vivo) ---
def obtener_dolares_vivos():
    try:
        mep = requests.get("https://dolarapi.com/v1/dolares/mep").json()['venta']
        oficial = requests.get("https://dolarapi.com/v1/dolares/oficial").json()['venta']
        brecha = ((mep / oficial) - 1) * 100
        return f"${mep:,.2f}", f"${oficial:,.2f}", f"{brecha:.1f}%"
    except:
        return "$1.424,34", "$1.415,00", "0.6%" # Respaldo por si cae la API externa

dolar_mep_vivo, dolar_oficial_vivo, brecha_viva = obtener_dolares_vivos()


# --- CONEXIÓN A GOOGLE SHEETS (4 PESTAÑAS) ---
# REEMPLAZÁ ACÁ: Poné tu ID real entre las comillas
SHEET_ID = "1zksr6ipnnKgYQJR8_H1PLdyiglmCAAaBe29Xb-8zCoY"

@st.cache_data(ttl=300) # Se actualiza automáticamente cada 5 minutos
def cargar_pestana(nombre_pestana):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
    try:
        return pd.read_csv(url)
    except:
        return None

# Cargamos las 4 fuentes de datos desde tu Sheets
df_home = cargar_pestana("Home_General")
df_semaforo = cargar_pestana("Semaforo_Sectores")
df_detalles = cargar_pestana("Detalle_Sectores")
df_series = cargar_pestana("Datos_Series")


# --- NAVEGACIÓN EN LA BARRA LATERAL ---
st.sidebar.title("📊 LUNES MACRO")
pantalla = st.sidebar.radio("Seleccioná la vista:", ["🏠 Presentación General", "🏢 Análisis por Sector"])

# 💡 CAMBIO AQUÍ: Si elige "Análisis por Sector", el selector aparece ACÁ, antes del USD
if pantalla == "🏢 Análisis por Sector":
    st.sidebar.divider()
    sectores_lista = ["Comercio minorista", "Comercio mayorista", "Gastronomía", "Construcción", "Servicios / Indumentaria", "Industria", "Automotriz", "Alimentos / Combustibles"]
    sector_sel = st.sidebar.selectbox("Elegí el Sector a analizar:", sectores_lista)

st.sidebar.divider()

# Mostrar SIEMPRE los dólares automáticos abajo de todo en la barra lateral
st.sidebar.markdown("### 💰 Mercado y Divisas *(En vivo)*")
with st.sidebar.container(border=True):
    st.sidebar.metric(label="Dólar MEP", value=dolar_mep_vivo)
    st.sidebar.metric(label="Dólar Oficial", value=dolar_oficial_vivo, delta=f"Brecha: {brecha_viva}", delta_color="inverse")


# =====================================================================
# VISTA 1: PRESENTACIÓN GENERAL (HOME)
# =====================================================================
if pantalla == "🏠 Presentación General":
    if df_home is not None and not df_home.empty:
        ultimo_informe = df_home.iloc[0]
        
        st.title(f"📊 LUNES MACRO — {str(ultimo_informe['Fecha'])}")
        st.divider()
        
        # 1. Cabecera de Impacto: Las 3 Claves de la semana
        st.markdown("### 🔑 3 Claves de esta Semana")
        with st.container(border=True):
            st.markdown(f"1️⃣ {ultimo_informe['Clave_1']}")
            st.markdown(f"2️⃣ {ultimo_informe['Clave_2']}")
            st.markdown(f"3️⃣ {ultimo_informe['Clave_3']}")
            
        st.divider()
        
        # 2. El Semáforo de la Economía Real
        st.markdown("### 🚨 Semáforo: Estado de los Sectores")
        if df_semaforo is not None and not df_semaforo.empty:
            cols_semaforo = st.columns(4)
            for index, row in df_semaforo.iterrows():
                col_idx = index % 4
                with cols_semaforo[col_idx]:
                    color_str = str(row['Color']).lower().strip()
                    color_emoji = "🔴" if "rojo" in color_str else "🟡" if "amarillo" in color_str else "🟢"
                    st.metric(label=f"{color_emoji} {row['Sector']}", value=str(row['Estado (Texto que se lee)']))
        st.divider()
        
        # 3. Bloque Inflación (Nacional vs Tandil + Alta Frecuencia)
        st.markdown("### 📈 Inflación y Tasas")
        col_ipc, col_equilibra = st.columns([1, 1])
        
        with col_ipc:
            with st.container(border=True):
                st.markdown("**Índices de Precios del Mes**")
                c1, c2 = st.columns(2)
                c1.metric(label="Inflación Nacional", value=str(ultimo_informe['IPC_Nacional']))
                c2.metric(label="Inflación Tandil", value=str(ultimo_informe['IPC_Tandil']))
                
                st.markdown("---")
                c3, c4 = st.columns(2)
                c3.metric(label="IPC Interanual", value=str(ultimo_informe['IPC_Interanual']))
                c4.metric(label="IPC Acumulado", value=str(ultimo_informe['IPC_Acumulado']))
                
        with col_equilibra:
            with st.container(border=True):
                st.markdown(f"⚡ **Alta Frecuencia (Equilibra): {str(ultimo_informe['Equilibra_Semanal'])}**")
                st.caption("Contexto y Regulados:")
                st.write(str(ultimo_informe['Equilibra_Contexto']))
                
    else:
        st.error("No se pudieron cargar los datos de la pestaña 'Home_General'.")


# =====================================================================
# VISTA 2: ANÁLISIS DETALLADO POR SECTOR
# =====================================================================
elif pantalla == "🏢 Análisis por Sector":
    # El selector ya se ejecutó en la barra lateral, así que procesamos directamente con 'sector_sel'
    st.title(f"Sector: {sector_sel}")
    st.divider()
    
    if df_detalles is not None and not df_detalles.empty:
        df_sec = df_detalles[df_detalles['Sector'] == sector_sel]
        
        if not df_sec.empty:
            info_sector = df_sec.iloc[0]
            
            # Tarjeta de KPI principal del sector
            st.markdown(f"### 📌 {info_sector['KPI_Nombre']}")
            st.subheader(str(info_sector['KPI_Valor']))
            st.divider()
            
            # Las 4 pestañas internas
            t_noticias, t_grafico, t_precios, t_micro = st.tabs([
                "📰 Novedades y Análisis", 
                "📊 Serie de Tiempo",
                "📋 Pizarra de Precios Ref.", 
                "🔍 Micro-Consumo / Curiosidades"
            ])
            
            # ---- SOLAPA 1: NOVEDADES Y ANÁLISIS ----
            with t_noticias:
                st.markdown("### Análisis de Coyuntura Semanal")
                st.info(str(info_sector['Analisis_Semanal']))
                
                if pd.notna(info_sector['Links_Fuentes']):
                    st.markdown("**Fuentes y portales de interés:**")
                    for link in str(info_sector['Links_Fuentes']).split(","):
                        link = link.strip()
                        if link.startswith("http"):
                            st.markdown(f"🔗 [Acceder a la Fuente Externa]({link})")
            
            # ---- SOLAPA 2: SERIE DE TIEMPO (Gráficos interactivos) ----
            with t_grafico:
                st.markdown("### 📈 Evolución Histórica del Sector")
                if df_series is not None and not df_series.empty:
                    df_geo = df_series[df_series['Sector'] == sector_sel].copy()
                    if not df_geo.empty:
                        df_geo['Fecha'] = pd.to_datetime(df_geo['Fecha'])
                        df_geo = df_geo.sort_values(by='Fecha')
                        
                        df_geo['Valor'] = df_geo['Valor'].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
                        df_geo['Valor'] = pd.to_numeric(df_geo['Valor'], errors='coerce')
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=df_geo['Fecha'], 
                            y=df_geo['Valor'], 
                            mode='lines+markers', 
                            name=sector_sel, 
                            line=dict(color='#0083B0', width=3),
                            fill='tozeroy',
                            fillcolor='rgba(0, 131, 176, 0.05)'
                        ))
                        fig.update_layout(
                            template="plotly_white", 
                            margin=dict(l=20, r=20, t=20, b=20),
                            xaxis_title="Período / Mes",
                            yaxis_title="Valor / Índice"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No hay datos numéricos cargados para este sector en la pestaña 'Datos_Series'.")
                else:
                    st.error("No se pudo leer la pestaña 'Datos_Series' del Google Sheet.")
            
            # ---- SOLAPA 3: PIZARRA DE PRECIOS DE REFERENCIA ----
            with t_precios:
                st.markdown("### Valores y Costos de Referencia en el Mercado")
                st.text(str(info_sector['Precios_Referencia']))
                
            # ---- SOLAPA 4: MICRO-CONSUMO / CURIOSIDADES ----
            with t_micro:
                st.markdown("### Datos de Comportamiento y Consumo Específico")
                st.warning(str(info_sector['Micro_Consumo']))
                
        else:
            st.warning(f"No hay novedades cargadas para el sector {sector_sel} esta semana.")
