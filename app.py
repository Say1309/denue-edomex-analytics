import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# Configuración Visual de la Aplicación
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Market Intelligence | DENUE Edomex",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .stMetric {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Intelligence & Market Benchmarking")
st.caption("Análisis comparativo de densidad comercial y viabilidad de mercado basada en datos del DENUE (INEGI) - Estado de México")

# -----------------------------------------------------------------------------
# Carga Eficiente con DuckDB
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    con = duckdb.connect()
    # Lectura directa desde el Parquet optimizado
    df = con.execute("SELECT * FROM 'data/denue_edomex_para_app.parquet'").fetchdf()
    con.close()
    return df

df_base = load_data()

# -----------------------------------------------------------------------------
# Barra Lateral - Filtros
# -----------------------------------------------------------------------------
st.sidebar.header("🎯 Parámetros del Análisis")

municipios_disponibles = sorted(df_base["municipio"].dropna().unique())

# Municipios sugeridos por defecto
defaults_mun = [m for m in ["Cocotitlán", "Chalco", "Ixtapaluca"] if m in municipios_disponibles]
if not defaults_mun:
    defaults_mun = municipios_disponibles[:2]

municipios_sel = st.sidebar.multiselect(
    "1. Selecciona los municipios a comparar:",
    options=municipios_disponibles,
    default=defaults_mun
)

if not municipios_sel:
    st.info("👋 Por favor selecciona al menos un municipio en el menú lateral para comenzar.")
    st.stop()

# Filtrado inicial por municipio
df_mun = df_base[df_base["municipio"].isin(municipios_sel)]

# Filtro dinámico por Giro / Actividad
giros_disponibles = sorted(df_mun["nombre_act"].dropna().unique())
giros_sel = st.sidebar.multiselect(
    "2. Filtrar por Giros Específicos (Opcional):",
    options=giros_disponibles,
    default=[],
    help="Deja este campo vacío para analizar la totalidad de los giros económicos."
)

if giros_sel:
    df_filtrado = df_mun[df_mun["nombre_act"].isin(giros_sel)]
else:
    df_filtrado = df_mun.copy()

# -----------------------------------------------------------------------------
# Panel Principal - KPIs
# -----------------------------------------------------------------------------
total_unidades = df_filtrado["total_establecimientos"].sum()
total_giros = df_filtrado["nombre_act"].nunique()
mun_count = len(municipios_sel)

c1, c2, c3 = st.columns(3)
c1.metric("Establecimientos Totales", f"{total_unidades:,}")
c2.metric("Giros Representados", f"{total_giros:,}")
c3.metric("Municipios en Comparativa", f"{mun_count}")

st.markdown("---")

# -----------------------------------------------------------------------------
# Estructura por Pestañas (Tabs)
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Panorama General", "🔍 Análisis por Giro", "📋 Vista de Datos"])

# -----------------------------------------------------------------------------
# TAB 1: PANORAMA GENERAL
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Top Giros Comerciales con Mayor Competencia")
    
    # Agregación Top 15
    top_giros = (
        df_filtrado.groupby(["municipio", "nombre_act"])["total_establecimientos"]
        .sum()
        .reset_index()
    )
    
    top_15_nombres = (
        top_giros.groupby("nombre_act")["total_establecimientos"]
        .sum()
        .nlargest(12)
        .index
    )
    
    df_top12 = top_giros[top_giros["nombre_act"].isin(top_15_nombres)]
    
    fig_bar = px.bar(
        df_top12,
        x="total_establecimientos",
        y="nombre_act",
        color="municipio",
        barmode="group",
        orientation="h",
        labels={
            "total_establecimientos": "Número de Negocios",
            "nombre_act": "Giro Comercial",
            "municipio": "Municipio"
        },
        height=500,
        template="plotly_dark"
    )
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_bar, use_container_width=True)

    # Distribución por tamaño de empresa
    st.subheader("Composición por Tamaños de Unidad Económica")
    df_tamano = (
        df_filtrado.groupby(["municipio", "tamano_empresa"])["total_establecimientos"]
        .sum()
        .reset_index()
    )
    
    fig_stack = px.bar(
        df_tamano,
        x="municipio",
        y="total_establecimientos",
        color="tamano_empresa",
        barmode="stack",
        labels={
            "total_establecimientos": "Cantidad de Negocios",
            "tamano_empresa": "Estrato de Personal",
            "municipio": "Municipio"
        },
        height=400,
        template="plotly_dark"
    )
    st.plotly_chart(fig_stack, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: ANÁLISIS DETALLADO POR GIRO
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Comparativa Específica entre Municipios")
    
    giro_foco = st.selectbox(
        "Selecciona un Giro Específico para comparar la presencia exacta:",
        options=sorted(df_mun["nombre_act"].dropna().unique())
    )
    
    df_foco = df_mun[df_mun["nombre_act"] == giro_foco]
    resumen_foco = df_foco.groupby("municipio")["total_establecimientos"].sum().reset_index()
    
    col_chart, col_stats = st.columns([2, 1])
    
    with col_chart:
        fig_foco = px.pie(
            resumen_foco,
            names="municipio",
            values="total_establecimientos",
            title=f"Distribución porcentual de: '{giro_foco}'",
            hole=0.4,
            template="plotly_dark"
        )
        st.plotly_chart(fig_foco, use_container_width=True)
        
    with col_stats:
        st.markdown(f"#### 💡 Métricas Clave: *{giro_foco}*")
        for idx, row in resumen_foco.iterrows():
            st.metric(f"Negocios en {row['municipio']}", f"{row['total_establecimientos']:,}")

# -----------------------------------------------------------------------------
# TAB 3: VISTA DE DATOS Y DESCARGA
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Explorador de Datos Filtrados")
    st.dataframe(df_filtrado, use_container_width=True, height=400)
    
    # Botón para descargar CSV directamente desde la app
    csv_data = df_filtrado.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 Descargar esta selección en CSV",
        data=csv_data,
        file_name="analisis_mercado_edomex.csv",
        mime="text/csv"
    )