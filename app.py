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

# Cargar datos desde Google Sheets con refresco rápido
@st.cache_data(ttl=15)
def cargar_datos():
    df = pd.read_csv(URL_CSV)
    
    # Normalizar columnas numéricas
    cols_num = ['P&S requeridos', 'p&s tramitados', 'P&S_EFI', 'P&S_EXT', 'P&S_SGH']
    for c in cols_num:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        else:
            df[c] = 0
            
    return df

try:
    df = cargar_datos()
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.stop()

# 3. FILTROS DINÁMICOS EN LA BARRA LATERAL (SIDEBAR)
st.sidebar.header("🔍 Filtros de Visualización")

resp_list = ["Todos"] + sorted([str(x) for x in df['Distribucción'].dropna().unique()])
sel_resp = st.sidebar.selectbox("Responsable (Distribución)", resp_list)

dir_list = ["Todos"] + sorted([str(x) for x in df['Director responsable'].dropna().unique()])
sel_dir = st.sidebar.selectbox("Director Responsable", dir_list)

cat_list = ["Todos"] + sorted([str(x) for x in df['categoria de compra'].dropna().unique()])
sel_cat = st.sidebar.selectbox("Categoría de Compra", cat_list)

area_list = ["Todos"] + sorted([str(x) for x in df['Area Responsable'].dropna().unique()])
sel_area = st.sidebar.selectbox("Área Responsable", area_list)

# Aplicar filtros dinámicos
df_filtrado = df.copy()

if sel_resp != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Distribucción'] == sel_resp]
if sel_dir != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Director responsable'] == sel_dir]
if sel_cat != "Todos":
    df_filtrado = df_filtrado[df_filtrado['categoria de compra'] == sel_cat]
if sel_area != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Area Responsable'] == sel_area]

# 4. TARJETAS DE INDICADORES CLAVE GENERALES
total_prov = len(df_filtrado)
req_total = int(df_filtrado['P&S requeridos'].sum())
tramitados_total = int(df_filtrado['p&s tramitados'].sum())

if req_total > 0:
    pct_avance_real = (tramitados_total / req_total) * 100
else:
    pct_avance_real = 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Proveedores", total_prov)
col2.metric("P&S Requeridos", req_total)
col3.metric("P&S Tramitados", tramitados_total, delta=f"{pct_avance_real:.1f}% Avance")
col4.metric("% Avance Real Global", f"{pct_avance_real:.1f}%")

st.markdown("---")

# 5. CÁLCULO Y DISTRIBUCIÓN DE P&S RECIBIDOS POR COMPAÑÍA
# Función para desglosar la columna 'p&s tramitados' (M) entre las columnas J, K, L
def calcular_recibidos(row):
    tramitados = row['p&s tramitados']
    rec_efi = 1 if (row['P&S_EFI'] == 1 and tramitados >= 1) else 0
    
    # Evaluar Extras S.A.
    if row['P&S_EXT'] == 1:
        if row['P&S_EFI'] == 1 and tramitados >= 2:
            rec_ext = 1
        elif row['P&S_EFI'] == 0 and tramitados >= 1:
            rec_ext = 1
        else:
            rec_ext = 0
    else:
        rec_ext = 0

    # Evaluar Eficacia SGH
    if row['P&S_SGH'] == 1:
        if tramitados >= row['P&S requeridos'] and row['P&S requeridos'] > 0:
            rec_sgh = 1
        else:
            rec_sgh = 0
    else:
        rec_sgh = 0

    return pd.Series([rec_efi, rec_ext, rec_sgh])

# Generar columnas de recibidos por fila
df_filtrado[['Rec_EFI', 'Rec_EXT', 'Rec_SGH']] = df_filtrado.apply(calcular_recibidos, axis=1)

# Totales requeridos vs recibidos
total_efi_req = int(df_filtrado['P&S_EFI'].sum())
total_ext_req = int(df_filtrado['P&S_EXT'].sum())
total_sgh_req = int(df_filtrado['P&S_SGH'].sum())

recibidos_efi = int(df_filtrado['Rec_EFI'].sum())
recibidos_ext = int(df_filtrado['Rec_EXT'].sum())
recibidos_sgh = int(df_filtrado['Rec_SGH'].sum())

st.subheader("🏢 Distribución de Paz y Salvos Recibidos por Compañía")

c_emp1, c_emp2 = st.columns([1, 2])

with c_emp1:
    st.markdown("**Totales Recibidos / Requeridos:**")
    st.metric("Eficacia S.A. (Recibidos)", f"{recibidos_efi} / {total_efi_req}")
    st.metric("Extras S.A. (Recibidos)", f"{recibidos_ext} / {total_ext_req}")
    st.metric("Eficacia SGH (Recibidos)", f"{recibidos_sgh} / {total_sgh_req}")

with c_emp2:
    df_companias = pd.DataFrame({
        'Compañía': ['Eficacia S.A.', 'Extras S.A.', 'Eficacia SGH'],
        'Paz y Salvos Recibidos': [recibidos_efi, recibidos_ext, recibidos_sgh]
    })
    
    fig_comp = px.pie(
        df_companias, 
        values='Paz y Salvos Recibidos', 
        names='Compañía', 
        hole=0.4,
        color='Compañía',
        color_discrete_map={'Eficacia S.A.': '#1E3A8A', 'Extras S.A.': '#0284C7', 'Eficacia SGH': '#38BDF8'}
    )
    fig_comp.update_traces(textposition='inside', textinfo='percent+label+value')
    st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")

# 6. GRÁFICOS DE AVANCE POR RESPONSABLE Y ÁREA RESPONSABLE
g1, g2 = st.columns(2)

with g1:
    st.subheader("📊 Avance por Responsable (Distribución)")
    df_resp = df_filtrado.groupby('Distribucción')[['P&S requeridos', 'p&s tramitados']].sum().reset_index()
    df_resp['% Avance'] = (df_resp['p&s tramitados'] / df_resp['P&S requeridos'] * 100).fillna(0)
    fig1 = px.bar(
        df_resp, x='Distribucción', y='% Avance',
        text_auto='.1f', color='% Avance', color_continuous_scale="Blues",
        hover_data=['P&S requeridos', 'p&s tramitados']
    )
    st.plotly_chart(fig1, use_container_width=True)

with g2:
    st.subheader("🏢 Avance por Área Responsable")
    df_area = df_filtrado.groupby('Area Responsable')[['P&S requeridos', 'p&s tramitados']].sum().reset_index()
    df_area['% Avance'] = (df_area['p&s tramitados'] / df_area['P&S requeridos'] * 100).fillna(0)
    # Filtrar solo áreas que tengan requerimientos activos
    df_area = df_area[df_area['P&S requeridos'] > 0]
    fig2 = px.bar(
        df_area, x='Area Responsable', y='% Avance',
        text_auto='.1f', color='% Avance', color_continuous_scale="Greens",
        hover_data=['P&S requeridos', 'p&s tramitados']
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# 7. AVANCE POR CATEGORÍA DE COMPRA
st.subheader("🏷️ Avance por Categoría de Compra")
df_cat = df_filtrado.groupby('categoria de compra')[['P&S requeridos', 'p&s tramitados']].sum().reset_index()
df_cat['% Avance'] = (df_cat['p&s tramitados'] / df_cat['P&S requeridos'] * 100).fillna(0)
df_cat = df_cat[df_cat['P&S requeridos'] > 0].sort_values(by='% Avance', ascending=True)

fig_cat = px.bar(
    df_cat, 
    y='categoria de compra', 
    x='% Avance',
    orientation='h',
    text_auto='.1f', 
    color='% Avance', 
    color_continuous_scale="Purples",
    hover_data=['P&S requeridos', 'p&s tramitados'],
    labels={'categoria de compra': 'Categoría de Compra', '% Avance': '% Avance Tramitado'}
)
fig_cat.update_layout(height=max(400, len(df_cat) * 25))
st.plotly_chart(fig_cat, use_container_width=True)

st.markdown("---")

# 8. TABLA DETALLADA
st.subheader("📋 Detalle Filtrado de Proveedores")
columnas_mostrar = ['PROVEEDOR', 'categoria de compra', 'Area Responsable', 'Director responsable', 'Distribucción', 'P&S_EFI', 'P&S_EXT', 'P&S_SGH', 'P&S requeridos', 'p&s tramitados', 'avance', 'Resultado Envío Script']
cols_existentes = [c for c in columnas_mostrar if c in df_filtrado.columns]

st.dataframe(df_filtrado[cols_existentes], use_container_width=True)
