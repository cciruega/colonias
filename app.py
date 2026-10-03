import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración General de la Página
st.set_page_config(page_title="Portal Operativo y de Mercado", layout="wide", page_icon="📊")

# 2. Carga de Datos (Cacheada para rendimiento)
@st.cache_data
def load_data():
    # Asegúrate de que "Colonia (7).xlsx" esté en la misma ruta que el script
    return pd.read_excel("Colonia (7).xlsx")

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error al cargar el archivo excel: {e}")
    st.stop()

df = df_raw.copy()

# ==========================================
# 3. PANEL LATERAL - FILTROS EN CASCADA
# ==========================================
st.sidebar.header("🔍 Filtros de Ubicación")
st.sidebar.markdown("Filtra la información para actualizar los indicadores.")

# Filtro 1: Area Rnum
areas_disp = sorted(df['Area Rnum'].dropna().unique())
area_rnum = st.sidebar.multiselect("Área Rnum", options=areas_disp)
if area_rnum:
    df = df[df['Area Rnum'].isin(area_rnum)]

# Filtro 2: Estado (Depende del Área)
estados_disp = sorted(df['Estado'].dropna().unique())
estado = st.sidebar.multiselect("Estado", options=estados_disp)
if estado:
    df = df[df['Estado'].isin(estado)]

# Filtro 3: Municipio (Depende del Estado)
municipios_disp = sorted(df['Municipio'].dropna().unique())
municipio = st.sidebar.multiselect("Municipio", options=municipios_disp)
if municipio:
    df = df[df['Municipio'].isin(municipio)]

# Filtro 4: Colonia C (Depende del Municipio)
colonias_disp = sorted(df['Colonia C'].dropna().unique())
colonia = st.sidebar.multiselect("Colonia C", options=colonias_disp)
if colonia:
    df = df[df['Colonia C'].isin(colonia)]


# ==========================================
# 4. ÁREA PRINCIPAL - KPIs (Indicadores Clave)
# ==========================================
st.title("📡 Panel de Indicadores Operativos por Colonia")
st.markdown("Visión ejecutiva de infraestructura, mercado y competencia.")
st.markdown("---")

# Cálculos rápidos
puertos_inst = int(df['Puertos Instalados'].sum(skipna=True))
puertos_disp = int(df['Puertos Disponibles'].sum(skipna=True))
clientes_inf = int(df['Clientes Infinitum'].sum(skipna=True))
ocupacion_prom = df['% Ocupación'].mean(skipna=True) * 100

# Tarjetas visuales
col1, col2, col3, col4 = st.columns(4)
col1.metric("Puertos Instalados", f"{puertos_inst:,}")
col2.metric("Puertos Disponibles", f"{puertos_disp:,}")
col3.metric("Clientes Infinitum", f"{clientes_inf:,}")
col4.metric("Ocupación Promedio", f"{ocupacion_prom:.1f}%" if pd.notna(ocupacion_prom) else "0.0%")
st.markdown("---")

# ==========================================
# 5. GRÁFICAS INTERACTIVAS
# ==========================================
st.subheader("Visualizaciones Principales")

# Pestañas para organizar la información sin saturar la pantalla
tab1, tab2, tab3 = st.tabs(["📊 Infraestructura y Clientes", "🥊 Competencia y Mercado", "📉 Análisis de Bajas"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        # Gráfica: Puertos por Municipio (Top 15)
        df_puertos = df.groupby('Municipio')[['Puertos Instalados', 'Puertos Disponibles']].sum().reset_index()
        df_puertos = df_puertos.sort_values(by='Puertos Instalados', ascending=False).head(15)
        fig_puertos = px.bar(df_puertos, x='Municipio', y=['Puertos Instalados', 'Puertos Disponibles'],
                             barmode='group', title="Top 15 Municipios por Infraestructura (Puertos)")
        st.plotly_chart(fig_puertos, use_container_width=True)
    
    with c2:
        # Gráfica: Distribución del tipo de cliente
        df_clientes = pd.DataFrame({
            'Segmento': ['Residencial', 'PyME', 'Empresarial'],
            'Total': [df['Infinitum Residencial'].sum(), df['Infinitum PyME'].sum(), df['Infinitum Empresarial'].sum()]
        })
        fig_clientes = px.pie(df_clientes, names='Segmento', values='Total', hole=0.4, 
                              title="Mix de Clientes Infinitum", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_clientes, use_container_width=True)

with tab2:
    c3, c4 = st.columns(2)
    with c3:
        # Gráfica: Penetración del Mayor Competidor
        # Nota: Ajustado para considerar el espacio en blanco al final del nombre en tu Excel
        col_comp = 'Mayor Competidor  ' if 'Mayor Competidor  ' in df.columns else 'Mayor Competidor'
        df_comp = df[col_comp].value_counts().reset_index()
        df_comp.columns = ['Competidor', 'Cantidad de Colonias']
        fig_comp = px.bar(df_comp, x='Competidor', y='Cantidad de Colonias', 
                          title="Presencia del Principal Competidor (por # de Colonias)", color='Competidor')
        st.plotly_chart(fig_comp, use_container_width=True)
        
    with c4:
        # Gráfica: Paquetes Más Vendidos
        df_paq = df['Paquete Mas Vendido'].value_counts().reset_index().head(5)
        df_paq.columns = ['Paquete', 'Frecuencia']
        fig_paq = px.bar(df_paq, x='Frecuencia', y='Paquete', orientation='h', 
                         title="Top 5 - Paquetes Más Vendidos", color='Paquete')
        fig_paq.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_paq, use_container_width=True)

with tab3:
    # Gráfica: Bajas por Portabilidad (Competencia)
    cols_bajas = ['Bajas Porta Izzi', 'Bajas Porta Megacable', 'Bajas Porta Totalplay', 'Bajas Porta Otros']
    cols_bajas_existentes = [c for c in cols_bajas if c in df.columns]
    
    if cols_bajas_existentes:
        df_bajas = df[cols_bajas_existentes].sum().reset_index()
        df_bajas.columns = ['Compañía', 'Total de Bajas']
        df_bajas['Compañía'] = df_bajas['Compañía'].str.replace('Bajas Porta ', '') # Limpieza de etiquetas
        
        fig_bajas = px.bar(df_bajas, x='Compañía', y='Total de Bajas', 
                           title="Pérdidas por Portabilidad a la Competencia", color='Compañía')
        st.plotly_chart(fig_bajas, use_container_width=True)
    else:
        st.info("No se encontraron datos de bajas por portabilidad en la selección actual.")

# ==========================================
# 6. TABLA DETALLADA DE DATOS
# ==========================================
st.markdown("---")
st.subheader("📋 Base de Datos Exploratoria")
st.write(f"Mostrando **{df.shape[0]}** registros según los filtros seleccionados.")

# Mostrar DataFrame (ocultando columnas que sean 100% NaN para tener una vista más limpia)
st.dataframe(df.dropna(axis=1, how='all'), use_container_width=True)

# Botón de Descarga
csv_data = df.to_csv(index=False).encode('utf-8-sig')
st.download_button(
    label="📥 Descargar información filtrada (CSV)",
    data=csv_data,
    file_name='datos_operativos_filtrados.csv',
    mime='text/csv'
)
