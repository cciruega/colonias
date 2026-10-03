import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración General
st.set_page_config(page_title="Portal Operativo y de Mercado", layout="wide", page_icon="📊")

# ==========================================
# 2. SISTEMA DE LOGIN
# ==========================================
def check_password():
    """Valida el usuario y contraseña."""
    def password_entered():
        if (st.session_state["username"] in st.secrets["passwords"] and 
            st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]):
            st.session_state["password_correct"] = True
            # Agrega esta línea para guardar el usuario de forma permanente:
            st.session_state["usuario_actual"] = st.session_state["username"]
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Acceso al Portal Operativo")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Iniciar sesión", on_click=password_entered)
        st.info("¿No tienes cuenta? Solicita tu acceso con el administrador.")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 Acceso al Portal Operativo")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Iniciar sesión", on_click=password_entered)
        st.error("❌ Usuario o contraseña incorrectos.")
        st.info("¿No tienes cuenta? Solicita tu acceso con el administrador.")
        return False
    return True

# ==========================================
# 3. CÓDIGO PRINCIPAL DEL PORTAL (Todo esto va IDENTADO hacia la derecha)
# ==========================================
if check_password():
    # Usamos la variable segura "usuario_actual" en lugar de "username"
    st.sidebar.success(f"👤 Sesión iniciada: **{st.session_state['usuario_actual']}**")
    
    # Botón para cerrar sesión
    if st.sidebar.button("Cerrar sesión"):
        del st.session_state["password_correct"]
        del st.session_state["usuario_actual"] # Borramos la variable segura al salir
        st.rerun()

    # --- A PARTIR DE AQUÍ TODO LLEVA UNA TABULACIÓN (ESPACIOS) ---
    
    # Carga de Datos
    @st.cache_data
    def load_data():
        return pd.read_excel("Colonia (7).xlsx")

    try:
        df_raw = load_data()
    except Exception as e:
        st.error(f"Error al cargar el archivo excel: {e}")
        st.stop()

    df = df_raw.copy()

    # Filtros Laterales
    st.sidebar.header("🔍 Filtros de Ubicación")
    
    if 'Area Rnum' in df.columns:
        areas_disp = sorted(df['Area Rnum'].dropna().unique())
        area_rnum = st.sidebar.multiselect("Área Rnum", options=areas_disp)
        if area_rnum:
            df = df[df['Area Rnum'].isin(area_rnum)]

    if 'Zona' in df.columns:
        zonas_disp = sorted(df['Zona'].dropna().unique())
        zona = st.sidebar.multiselect("Zona", options=zonas_disp)
        if zona:
            df = df[df['Zona'].isin(zona)]
            
    if 'Estado' in df.columns:
        estados_disp = sorted(df['Estado'].dropna().unique())
        estado = st.sidebar.multiselect("Estado", options=estados_disp)
        if estado:
            df = df[df['Estado'].isin(estado)]
            
    if 'Municipio' in df.columns:
        municipios_disp = sorted(df['Municipio'].dropna().unique())
        municipio = st.sidebar.multiselect("Municipio", options=municipios_disp)
        if municipio:
            df = df[df['Municipio'].isin(municipio)]
            
    if 'Colonia C' in df.columns:
        colonias_disp = sorted(df['Colonia C'].dropna().unique())
        colonia = st.sidebar.multiselect("Colonia C", options=colonias_disp)
        if colonia:
            df = df[df['Colonia C'].isin(colonia)]

    # Área Principal
    st.title("📡 Panel de Indicadores por Colonia")
    st.markdown("Visión ejecutiva de infraestructura, mercado y competencia.")
    st.markdown("---")

    # Cálculos
    puertos_inst = int(df['Puertos Instalados'].sum(skipna=True))
    puertos_disp = int(df['Puertos Disponibles'].sum(skipna=True))
    clientes_inf = int(df['Clientes Infinitum'].sum(skipna=True))
    ocupacion_prom = df['% Ocupación'].mean(skipna=True) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Puertos Instalados", f"{puertos_inst:,}")
    col2.metric("Puertos Disponibles", f"{puertos_disp:,}")
    col3.metric("Clientes Infinitum", f"{clientes_inf:,}")
    col4.metric("Ocupación Promedio", f"{ocupacion_prom:.1f}%" if pd.notna(ocupacion_prom) else "0.0%")
    st.markdown("---")

    # Gráficas
    st.subheader("Visualizaciones Principales")
    tab1, tab2, tab3 = st.tabs(["📊 Infraestructura y Clientes", "🥊 Competencia y Mercado", "📉 Análisis de Bajas"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            df_puertos = df.groupby('Municipio')[['Puertos Instalados', 'Puertos Disponibles']].sum().reset_index()
            df_puertos = df_puertos.sort_values(by='Puertos Instalados', ascending=False).head(15)
            fig_puertos = px.bar(df_puertos, x='Municipio', y=['Puertos Instalados', 'Puertos Disponibles'], barmode='group')
            st.plotly_chart(fig_puertos, use_container_width=True)
        with c2:
            df_clientes = pd.DataFrame({'Segmento': ['Residencial', 'PyME', 'Empresarial'],
                                        'Total': [df['Infinitum Residencial'].sum(), df['Infinitum PyME'].sum(), df['Infinitum Empresarial'].sum()]})
            fig_clientes = px.pie(df_clientes, names='Segmento', values='Total', hole=0.4)
            st.plotly_chart(fig_clientes, use_container_width=True)

    with tab2:
        c3, c4 = st.columns(2)
        with c3:
            col_comp = 'Mayor Competidor  ' if 'Mayor Competidor  ' in df.columns else 'Mayor Competidor'
            df_comp = df[col_comp].value_counts().reset_index()
            df_comp.columns = ['Competidor', 'Cantidad de Colonias']
            fig_comp = px.bar(df_comp, x='Competidor', y='Cantidad de Colonias', color='Competidor')
            st.plotly_chart(fig_comp, use_container_width=True)
        with c4:
            df_paq = df['Paquete Mas Vendido'].value_counts().reset_index().head(5)
            df_paq.columns = ['Paquete', 'Frecuencia']
            fig_paq = px.bar(df_paq, x='Frecuencia', y='Paquete', orientation='h', color='Paquete')
            fig_paq.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_paq, use_container_width=True)

    with tab3:
        cols_bajas = ['Bajas Porta Izzi', 'Bajas Porta Megacable', 'Bajas Porta Totalplay', 'Bajas Porta Otros']
        cols_bajas_existentes = [c for c in cols_bajas if c in df.columns]
        if cols_bajas_existentes:
            df_bajas = df[cols_bajas_existentes].sum().reset_index()
            df_bajas.columns = ['Compañía', 'Total de Bajas']
            df_bajas['Compañía'] = df_bajas['Compañía'].str.replace('Bajas Porta ', '')
            fig_bajas = px.bar(df_bajas, x='Compañía', y='Total de Bajas', color='Compañía')
            st.plotly_chart(fig_bajas, use_container_width=True)
        else:
            st.info("No se encontraron datos de bajas.")

    # Tabla Final
    st.markdown("---")
    st.subheader("📋 Base de Datos Exploratoria")
    st.dataframe(df.dropna(axis=1, how='all'), use_container_width=True)
    
    csv_data = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 Descargar datos", data=csv_data, file_name='datos.csv', mime='text/csv')
