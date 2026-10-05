import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Analizador Comercial Edomex | DENUE",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Analizador de Competencia y Oferta Comercial (Estado de México)")
st.markdown("""
Esta herramienta permite evaluar la estructura económica y densidad comercial de **uno o varios municipios colindantes** 
del Estado de México a partir del dataset procesado del **DENUE (INEGI)**.
""")

# Cargar datos usando DuckDB (Lectura ultra rápida de Parquet)
@st.cache_data
def load_data():
    con = duckdb.connect()
    df = con.execute("SELECT * FROM 'data/denue_edomex_para_app.parquet'").fetchdf()
    con.close()
    return df

df_base = load_data()

# -----------------------------------------------------------------------------
# Filtros en Barra Lateral
# -----------------------------------------------------------------------------
st.sidebar.header("🎯 Filtros de Selección")

# Lista ordenada de municipios
municipios_disponibles = sorted(df_base["municipio"].dropna().unique())

# Selector múltiple de municipios (por defecto Cocotitlán, Chalco e Ixtapaluca)
municipios_default = [m for m in municipios_disponibles if m in ["Cocotitlán", "Chalco", "Ixtapaluca"]]
if not municipios_default:
    municipios_default = municipios_disponibles[:2]

municipios_sel = st.sidebar.multiselect(
    "Selecciona 1, 2 o más municipios a comparar:",
    options=municipios_disponibles,
    default=municipios_default
)

if not municipios_sel:
    st.warning("Por favor selecciona al menos un municipio en el menú lateral.")
    st.stop()

# Filtrar dataframe
df_filtrado = df_base[df_base["municipio"].isin(municipios_sel)]

# -----------------------------------------------------------------------------
# KPIs Principales
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
total_unidades = df_filtrado["total_establecimientos"].sum()
total_giros = df_filtrado["nombre_act"].nunique()
mun_count = len(municipios_sel)

col1.metric("Unidades Económicas Totales", f"{total_unidades:,}")
col2.metric("Giros Comerciales Distintos", f"{total_giros:,}")
col3.metric("Municipios Seleccionados", f"{mun_count}")

st.markdown("---")

# -----------------------------------------------------------------------------
# Comparativa por Giro Económico (Top 15)
# -----------------------------------------------------------------------------
st.subheader("🏆 Top 15 Giros Comerciales con Mayor Competencia")

top_giros = (
    df_filtrado.groupby(["municipio", "nombre_act"])["total_establecimientos"]
    .sum()
    .reset_index()
    .sort_values(by="total_establecimientos", ascending=False)
)

top_15_nombres = (
    top_giros.groupby("nombre_act")["total_establecimientos"]
    .sum()
    .nlargest(15)
    .index
)

df_top15 = top_giros[top_giros["nombre_act"].isin(top_15_nombres)]

fig_bar = px.bar(
    df_top15,
    x="total_establecimientos",
    y="nombre_act",
    color="municipio",
    barmode="group",
    orientation="h",
    title="Comparativa de Negocios por Municipio y Giro Económico",
    labels={"total_establecimientos": "Número de Negocios", "nombre_act": "Giro / Actividad", "municipio": "Municipio"},
    height=600
)
fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------------------------------------------------------
# Desglose por Tamaño de Empresa
# -----------------------------------------------------------------------------
st.subheader("🏢 Distribución por Tamaño de Empresa")

df_tamano = (
    df_filtrado.groupby(["municipio", "tamano_empresa"])["total_establecimientos"]
    .sum()
    .reset_index()
)

fig_pie = px.bar(
    df_tamano,
    x="municipio",
    y="total_establecimientos",
    color="tamano_empresa",
    title="Composición por Tamaño de Unidad Económica",
    labels={"total_establecimientos": "Total Establecimientos", "tamano_empresa": "Tamaño", "municipio": "Municipio"},
    barmode="stack"
)
st.plotly_chart(fig_pie, use_container_width=True)

# Tabla de Datos
with st.expander("📄 Ver Tabla de Datos Completa"):
    st.dataframe(df_filtrado)