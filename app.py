import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# Configuración Visual
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Market Intelligence | DENUE Edomex",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
st.caption("Análisis comparativo de densidad comercial, oferta y microdatos del DENUE (INEGI) - Estado de México")

# -----------------------------------------------------------------------------
# Conexión a Base de Datos DuckDB
# -----------------------------------------------------------------------------
DB_PATH = "data/denue_analitica.duckdb"

@st.cache_resource
def get_db_connection():
    return duckdb.connect(DB_PATH, read_only=True)

con = get_db_connection()

# -----------------------------------------------------------------------------
# Barra Lateral - Filtros
# -----------------------------------------------------------------------------
st.sidebar.header("🎯 Parámetros del Análisis")

municipios_disponibles = [m[0] for m in con.execute("SELECT DISTINCT municipio FROM denue_microdatos WHERE municipio IS NOT NULL ORDER BY municipio").fetchall()]

defaults_mun = [m for m in ["Cocotitlán", "Chalco", "Ixtapaluca"] if m in municipios_disponibles]
if not defaults_mun and municipios_disponibles:
    defaults_mun = municipios_disponibles[:2]

municipios_sel = st.sidebar.multiselect(
    "1. Selecciona los municipios a comparar:",
    options=municipios_disponibles,
    default=defaults_mun
)

if not municipios_sel:
    st.info("👋 Por favor selecciona al menos un municipio en el menú lateral para comenzar.")
    st.stop()

muns_str = "', '".join(municipios_sel)

giros_disponibles = [g[0] for g in con.execute(f"SELECT DISTINCT nombre_act_limpio FROM denue_microdatos WHERE municipio IN ('{muns_str}') AND nombre_act_limpio IS NOT NULL ORDER BY nombre_act_limpio").fetchall()]

giros_sel = st.sidebar.multiselect(
    "2. Filtrar por Giros Específicos (Opcional):",
    options=giros_disponibles,
    default=[],
    help="Deja este campo vacío para analizar la totalidad de los giros económicos."
)

st.sidebar.markdown("---")
max_puntos_mapa = st.sidebar.slider("Puntos máximos en Mapa:", 1000, 25000, 10000, 1000)

# -----------------------------------------------------------------------------
# Consulta SQL Dinámica
# -----------------------------------------------------------------------------
query_base = f"SELECT * FROM denue_microdatos WHERE municipio IN ('{muns_str}')"
if giros_sel:
    giros_str = "', '".join(giros_sel)
    query_base += f" AND nombre_act_limpio IN ('{giros_str}')"

df_filtrado = con.execute(query_base).fetchdf()

if "nombre_act_limpio" in df_filtrado.columns:
    df_filtrado["nombre_act"] = df_filtrado["nombre_act_limpio"]

if "total_establecimientos" not in df_filtrado.columns:
    df_filtrado["total_establecimientos"] = 1

col_estrato = None
for c in ['per_ocu', 'estrato', 'personal', 'tamano_empresa']:
    if c in df_filtrado.columns:
        col_estrato = c
        break

if col_estrato and col_estrato != "tamano_empresa":
    df_filtrado["tamano_empresa"] = df_filtrado[col_estrato]

if 'latitud' in df_filtrado.columns:
    df_filtrado['latitud'] = pd.to_numeric(df_filtrado['latitud'], errors='coerce')
if 'longitud' in df_filtrado.columns:
    df_filtrado['longitud'] = pd.to_numeric(df_filtrado['longitud'], errors='coerce')

# -----------------------------------------------------------------------------
# Panel Principal - KPIs
# -----------------------------------------------------------------------------
total_unidades = df_filtrado["total_establecimientos"].sum()
total_giros = df_filtrado["nombre_act"].nunique()
mun_count = len(municipios_sel)

c1, c2, c3 = st.columns(3)
c1.metric("Establecimientos Totales (Oferta)", f"{total_unidades:,}")
c2.metric("Giros Representados", f"{total_giros:,}")
c3.metric("Municipios en Comparativa", f"{mun_count}")

st.markdown("---")

# -----------------------------------------------------------------------------
# Estructura por Pestañas (Tabs)
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Panorama General", 
    "🔍 Análisis por Giro", 
    "📋 Vista de Datos",
    "🗺️ Mapa & Geolocalización",
    "🏢 Listado & Ubicación Directa"
])

# TAB 1: PANORAMA GENERAL
with tab1:
    st.subheader("Top Giros Comerciales con Mayor Competencia (Oferta)")
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
            "total_establecimientos": "Número de Negocios (Oferta)",
            "nombre_act": "Giro Comercial",
            "municipio": "Municipio"
        },
        height=500,
        template="plotly_dark"
    )
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Composición por Tamaños de Unidad Económica (Estrato de Personal)")
    if "tamano_empresa" in df_filtrado.columns:
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

# TAB 2: ANÁLISIS DETALLADO POR GIRO
with tab2:
    st.subheader("Comparativa Específica entre Municipios")
    giros_disponibles_act = sorted(df_filtrado["nombre_act"].dropna().unique())
    if giros_disponibles_act:
        giro_foco = st.selectbox(
            "Selecciona un Giro Específico para comparar la presencia exacta:",
            options=giros_disponibles_act
        )
        df_foco = df_filtrado[df_filtrado["nombre_act"] == giro_foco]
        resumen_foco = df_foco.groupby("municipio")["total_establecimientos"].sum().reset_index()
        
        col_chart, col_stats = st.columns([2, 1])
        with col_chart:
            fig_foco = px.pie(
                resumen_foco,
                names="municipio",
                values="total_establecimientos",
                title=f"Distribución porcentual de la oferta: '{giro_foco}'",
                hole=0.4,
                template="plotly_dark"
            )
            st.plotly_chart(fig_foco, use_container_width=True)
        with col_stats:
            st.markdown(f"#### 💡 Métricas Clave (Oferta): *{giro_foco}*")
            for idx, row in resumen_foco.iterrows():
                st.metric(f"Negocios en {row['municipio']}", f"{row['total_establecimientos']:,}")

# TAB 3: VISTA DE DATOS
with tab3:
    st.subheader("Explorador General de Microdatos")
    st.dataframe(df_filtrado, width='stretch', height=400)
    csv_data = df_filtrado.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 Descargar esta selección en CSV",
        data=csv_data,
        file_name="analisis_mercado_edomex.csv",
        mime="text/csv"
    )

# TAB 4: MAPA DE GEOLOCALIZACIÓN GENERAL
with tab4:
    st.subheader("🗺️ Mapa Interactivo de Unidades Económicas")
    df_mapa_subset = df_filtrado.head(max_puntos_mapa)
    if not df_mapa_subset.empty and 'latitud' in df_mapa_subset.columns and 'longitud' in df_mapa_subset.columns:
        df_mapa_clean = df_mapa_subset.dropna(subset=['latitud', 'longitud'])
        st.map(df_mapa_clean, latitude='latitud', longitude='longitud', size=3, color='#FF4B4B')
        st.caption(f"Mostrando {len(df_mapa_clean):,} establecimientos geolocalizados.")

# TAB 5: LISTADO ÚNICO Y GEOLOCALIZACIÓN DIRECTA
with tab5:
    st.subheader("🏢 Directorio Único y Geolocalización Directa")
    st.markdown("Selecciona cualquier establecimiento del listado (sin duplicados) para ubicar su punto exacto en el mapa.")
    
    # Columnas prioritarias para la tabla
    candidatas = ['nom_estab', 'raz_social', 'nombre_act', 'per_ocu', 'municipio', 'latitud', 'longitud']
    cols_mostrar = [c for c in candidatas if c in df_filtrado.columns]
    
    # ELIMINAR DUPLICADOS EXACTOS POR NOMBRE, GIRO Y MUNICIPIO
    df_unico = df_filtrado[cols_mostrar].drop_duplicates(subset=['nom_estab', 'nombre_act', 'municipio']).reset_index(drop=True)
    
    col_lista, col_mapa_individual = st.columns([1.2, 1])
    
    with col_lista:
        st.markdown("### 📋 Directorio Unificado")
        # Permite seleccionar una fila de la tabla
        event = st.dataframe(
            df_unico,
            width='stretch',
            height=400,
            on_select="rerun",
            selection_mode="single-row"
        )
        
    with col_mapa_individual:
        st.markdown("### 📍 Ubicación en Mapa")
        filas_seleccionadas = event.selection.rows if event else []
        
        if filas_seleccionadas:
            idx_sel = filas_seleccionadas[0]
            negocio_sel = df_unico.iloc[idx_sel]
            
            st.success(f"**Establecimiento:** {negocio_sel.get('nom_estab', 'N/A')}")
            st.caption(f"**Giro:** {negocio_sel.get('nombre_act', 'N/A')} | **Municipio:** {negocio_sel.get('municipio', 'N/A')}")
            
            if pd.notnull(negocio_sel.get('latitud')) and pd.notnull(negocio_sel.get('longitud')):
                df_punto = pd.DataFrame([{
                    'latitud': float(negocio_sel['latitud']),
                    'longitud': float(negocio_sel['longitud'])
                }])
                st.map(df_punto, latitude='latitud', longitude='longitud', zoom=15, size=10, color='#00FF66')
            else:
                st.warning("Este establecimiento no cuenta con coordenadas válidas.")
        else:
            st.info("👈 Haz clic en cualquier fila de la tabla de la izquierda para centrar el mapa en ese negocio.")
