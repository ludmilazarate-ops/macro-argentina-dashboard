import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import re
import unicodedata

def normalizar(texto):
    if pd.isna(texto):
        return ""

    texto = str(texto).strip().lower()

    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

    return texto
# 1. Configuración de la aplicación web
st.set_page_config(
    page_title="Lunes Macro - Consultores", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos estéticos para solapas
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
        return "$1.424,34", "$1.415,00", "0.6%" 

dolar_mep_vivo, dolar_oficial_vivo, brecha_viva = obtener_dolares_vivos()


# --- CONEXIÓN A GOOGLE SHEETS (4 PESTAÑAS) ---
SHEET_ID = "1zksr6ipnnKgYQJR8_H1PLdyiglmCAAaBe29Xb-8zCoY"

@st.cache_data(ttl=600) 
def cargar_pestana(nombre_pestana):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
    try:
        return pd.read_csv(url)
    except:
        return None

# Cargamos las 4 fuentes de datos
df_home = cargar_pestana("Home_General")
df_semaforo = cargar_pestana("Semaforo_Sectores")
df_detalles = cargar_pestana("Detalle_Sectores")
df_series = cargar_pestana("Datos_Series")


# --- NAVEGACIÓN EN LA BARRA LATERAL ---
st.sidebar.title("📊 LUNES MACRO")
pantalla = st.sidebar.radio("Seleccioná la vista:", ["🏠 Presentación General", "🏢 Análisis por Sector"])

if pantalla == "🏢 Análisis por Sector":

    st.sidebar.divider()

    if df_detalles is not None and not df_detalles.empty:

        try:
            c_sector = [c for c in df_detalles.columns if 'sect' in c.lower()][0]

            sectores_lista = (
                df_detalles[c_sector]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            sectores_lista = sorted(sectores_lista)

        except:
            sectores_lista = []

    else:
        sectores_lista = []

    sector_sel = st.sidebar.selectbox(
        "Elegí el Sector a analizar:",
        sectores_lista
    )

st.sidebar.divider()

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
        
        st.markdown("### 🔑 3 Claves de esta Semana")
        with st.container(border=True):
            st.markdown(f"1️⃣ {ultimo_informe['Clave_1']}")
            st.markdown(f"2️⃣ {ultimo_informe['Clave_2']}")
            st.markdown(f"3️⃣ {ultimo_informe['Clave_3']}")
            
        st.divider()
        
        st.markdown("### 🚨 Semáforo: Estado de los Sectores")
        if df_semaforo is not None and not df_semaforo.empty:
            try:
                col_sector = [c for c in df_semaforo.columns if 'sect' in c.lower()][0]
                col_color = [c for c in df_semaforo.columns if 'color' in c.lower()][0]
                col_estado = [c for c in df_semaforo.columns if 'est' in c.lower() or 'text' in c.lower()][0]
                
                cols_semaforo = st.columns(4)
                for index, row in df_semaforo.iterrows():
                    col_idx = index % 4
                    with cols_semaforo[col_idx]:
                        color_str = str(row[col_color]).lower().strip()
                        color_emoji = "🔴" if "rojo" in color_str else "🟡" if "amarillo" in color_str else "🟢"
                        st.metric(label=f"{color_emoji} {row[col_sector]}", value=str(row[col_estado]))
            except:
                st.error("Revisá los títulos de la pestaña 'Semaforo_Sectores'.")
        st.divider()
        
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
# VISTA 2: ANÁLISIS DETALLADO POR SECTOR (VERSIÓN ANTIBALAS)
# =====================================================================
elif pantalla == "🏢 Análisis por Sector":
    st.title(f"Sector: {sector_sel}")
    st.divider()
    
    if df_detalles is not None and not df_detalles.empty:
        try:
            # Detectamos las columnas de la pestaña Detalle_Sectores de forma inteligente aproximada
            c_sector = [c for c in df_detalles.columns if 'sect' in c.lower()][0]
            c_kpi_nom = [c for c in df_detalles.columns if 'kpi_nom' in c.lower() or 'nom' in c.lower()][0]
            c_kpi_val = [c for c in df_detalles.columns if 'kpi_val' in c.lower() or 'val' in c.lower()][0]
            c_analisis = [c for c in df_detalles.columns if 'analis' in c.lower() or 'notic' in c.lower()][0]
            c_precios = [c for c in df_detalles.columns if 'prec' in c.lower() or 'ref' in c.lower()][0]
            c_micro = [c for c in df_detalles.columns if 'micro' in c.lower() or 'curios' in c.lower() or 'comport' in c.lower()][0]
            
            # Intentamos buscar la columna de links si existe, sino queda vacía
            c_links_list = [c for c in df_detalles.columns if 'link' in c.lower() or 'fuent' in c.lower()]
            c_links = c_links_list[0] if c_links_list else None
            
            # Filtrado inteligente por sector
         sector_busqueda = normalizar(sector_sel)

df_sec = df_detalles[
    df_detalles[c_sector]
    .astype(str)
    .apply(normalizar)
    .str.contains(sector_busqueda, na=False)
]
            
            if not df_sec.empty:
               info_sector = df_sec.iloc[0]

if len(df_sec) > 1:
    st.caption(f"Se encontraron {len(df_sec)} registros para este sector.")
                
                # Tarjeta de KPI principal
                st.markdown(f"### 📌 {info_sector[c_kpi_nom]}")
                st.subheader(str(info_sector[c_kpi_val]))
                st.divider()
                
                # Las 4 solapas internas
                t_noticias, t_grafico, t_precios, t_micro = st.tabs([
                    "📰 Novedades y Análisis", 
                    "📊 Serie de Tiempo",
                    "📋 Pizarra de Precios Ref.", 
                    "🔍 Micro-Consumo / Curiosidades"
                ])
                
                with t_noticias:
                    st.markdown("### Análisis de Coyuntura Semanal")
                    st.info(str(info_sector[c_analisis]))
                    
                    if c_links and pd.notna(info_sector[c_links]):
                        st.markdown("**Fuentes y portales de interés:**")
                     links = re.split(r'[,;\n]', str(info_sector[c_links]))

for link in links:

    link = link.strip()

    if link.startswith("http"):
        st.link_button("🔗 Abrir fuente", link)
                
                with t_grafico:
                    st.markdown("### 📈 Evolución Histórica del Sector")
                    if df_series is not None and not df_series.empty:
                        try:
                            c_ser_sec = [c for c in df_series.columns if 'sect' in c.lower()][0]
                            c_ser_fec = [c for c in df_series.columns if 'fech' in c.lower() or 'date' in c.lower()][0]
                            c_ser_val = [c for c in df_series.columns if 'val' in c.lower() or 'indic' in c.lower() or 'num' in c.lower()][-1]
                            
                            df_geo = df_series[df_series[c_ser_sec].astype(str).str.lower().str.strip() == sector_sel.lower().strip()].copy()
                            
                            if not df_geo.empty:
                                df_geo[c_ser_fec] = pd.to_datetime(df_geo[c_ser_fec])
                                df_geo = df_geo.sort_values(by=c_ser_fec)
                                
                                df_geo[c_ser_val] = df_geo[c_ser_val].astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False)
                                df_geo[c_ser_val] = pd.to_numeric(df_geo[c_ser_val], errors='coerce')
                                
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=df_geo[c_ser_fec], 
                                    y=df_geo[c_ser_val], 
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
                                    yaxis_title="Valor"
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("No hay datos numéricos cargados para este sector en la pestaña 'Datos_Series'.")
                    except Exception as e:
    st.error(f"Error al procesar el gráfico: {e}")
                    else:
                        st.error("No se pudo leer la pestaña 'Datos_Series' del Google Sheet.")
                
                with t_precios:
                    st.markdown("### Valores y Costos de Referencia en el Mercado")
                    st.text(str(info_sector[c_precios]))
                    
                with t_micro:
                    st.markdown("### Datos de Comportamiento y Consumo Específico")
                    st.warning(str(info_sector[c_micro]))
                    
            else:
                st.warning(f"No hay novedades cargadas para el sector {sector_sel} esta semana.")
    except Exception as e:
    st.error(f"Error en Detalle_Sectores: {e}")
