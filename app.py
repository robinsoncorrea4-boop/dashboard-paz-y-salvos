import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA WEB
st.set_page_config(
    page_title="Dashboard Paz y Salvos 2026-I | Eficacia",
    page_icon="📊",
    layout="wide"
)

# Título Principal
st.title("📊 Control y Avance de Paz y Salvos Semestral 2026-I")
st.caption("Eficacia S.A. | Área de Compras e Inventario")

# 2. ENLACE A TU GOOGLE SHEET (Pestaña 'proveedores', GID=144580645)
SHEET_ID = "1OEkm12emw4sUHjC5r2BdPa9FKBQV6J8TUnVKJi9K_5I"
GID = "144580645"
URL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# Función para cargar datos con caché de 30 segundos (para ver cambios en tiempo real)
@st.cache_data(ttl=30)
def cargar_datos():
    df = pd.read_csv(URL_CSV)
    
    # Limpiar y normalizar la columna de avance
    if 'avance' in df.columns:
        def convertir_avance(val):
            if pd.isna(val):
                return 0.0
            val_str = str(val).replace('%', '').strip()
            try:
                num = float(val_str)
                return num if num <= 1.0 else num / 100.0
            except:
                return 0.0
        
        df['avance_num'] = df['avance'].apply(convertir_avance)
    else:
        df['avance_num'] = 0.0
        
    return df

try:
    df = cargar_datos()
except Exception as e:
    st.error(f"Error al conectar con la hoja de Google Sheets: {e}")
    st.stop()

# 3. FILTROS DINÁMICOS EN LA BARRA LATERAL (SIDEBAR)
st.sidebar.header("🔍 Filtros de Visualización")

# Filtro 1: Responsable / Distribución
resp_list = ["Todos"] + sorted([str(x) for x in df['Distribucción'].dropna().unique()])
sel_resp = st.sidebar.selectbox("Responsable (Distribución)", resp_list)

# Filtro 2: Director Responsable
dir_list = ["Todos"] + sorted([str(x) for x in df['Director responsable'].dropna().unique()])
sel_dir = st.sidebar.selectbox("Director Responsable", dir_list)

# Filtro 3: Categoría de Compra
cat_list = ["Todos"] + sorted([str(x) for x in df['categoria de compra'].dropna().unique()])
sel_cat = st.sidebar.selectbox("Categoría de Compra", cat_list)

# Filtro 4: Área Responsable
area_list = ["Todos"] + sorted([str(x) for x in df['Area Responsable'].dropna().unique()])
sel_area = st.sidebar.selectbox("Área Responsable", area_list)

# Aplicar los filtros a los datos
df_filtrado = df.copy()

if sel_resp != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Distribucción'] == sel_resp]
if sel_dir != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Director responsable'] == sel_dir]
if sel_cat != "Todos":
    df_filtrado = df_filtrado[df_filtrado['categoria de compra'] == sel_cat]
if sel_area != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Area Responsable'] == sel_area]

# 4. TARJETAS DE INDICADORES CLAVE (KPIs)
total_prov = len(df_filtrado)
completados = len(df_filtrado[df_filtrado['avance_num'] >= 1.0])
pendientes = total_prov - completados
pct_promedio = (df_filtrado['avance_num'].mean() * 100) if total_prov > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Proveedores", total_prov)
col2.metric("Completados (100%)", completados, delta=f"{(completados/total_prov*100 if total_prov>0 else 0):.1f}%")
col3.metric("Pendientes", pendientes, delta=f"-{pendientes}", delta_color="inverse")
col4.metric("% Avance Promedio", f"{pct_promedio:.1f}%")

st.markdown("---")

# 5. GRÁFICOS INTERACTIVOS
g1, g2 = st.columns(2)

with g1:
    st.subheader("📊 Avance por Responsable (Distribución)")
    df_resp = df_filtrado.groupby('Distribucción')['avance_num'].mean().reset_index()
    df_resp['% Avance'] = df_resp['avance_num'] * 100
    fig1 = px.bar(
        df_resp, x='Distribucción', y='% Avance',
        text_auto='.1f', color='% Avance', color_continuous_scale="Blues"
    )
    st.plotly_chart(fig1, use_container_width=True)

with g2:
    st.subheader("👨‍💼 Avance por Director Responsable")
    df_dir = df_filtrado.groupby('Director responsable')['avance_num'].mean().reset_index()
    df_dir['% Avance'] = df_dir['avance_num'] * 100
    fig2 = px.bar(
        df_dir, x='Director responsable', y='% Avance',
        text_auto='.1f', color='% Avance', color_continuous_scale="Greens"
    )
    st.plotly_chart(fig2, use_container_width=True)

# 6. TABLA INTERACTIVA DETALLADA
st.subheader("📋 Detalle Filtrado de Proveedores")
columnas_mostrar = ['PROVEEDOR', 'categoria de compra', 'Area Responsable', 'Director responsable', 'Distribucción', 'avance', 'Resultado Envío Script']
cols_existentes = [c for c in columnas_mostrar if c in df_filtrado.columns]

st.dataframe(df_filtrado[cols_existentes], use_container_width=True)
