import pandas as pd
import numpy as np

print("--- 1. CARGANDO DATASET ---")
path_parquet = "data/denue_edomex_para_app.parquet"
df = pd.read_parquet(path_parquet)

print(f"Registros totales: {len(df):,}")
print(f"Giros únicos iniciales: {df['nombre_act'].nunique():,}")

# --- 2. REGISTRO DE ESTRUCTURA Y COLUMNAS ---
info_columnas = []
for col in df.columns:
    info_columnas.append({
        "columna": col,
        "tipo_dato": str(df[col].dtype),
        "valores_no_nulos": int(df[col].count()),
        "ejemplo_valor": str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "N/A"
    })

df_cols = pd.DataFrame(info_columnas)
df_cols.to_csv("estructura_columnas_parquet.csv", index=False, encoding="utf-8-sig")
print("-> Estructura de columnas exportada a: estructura_columnas_parquet.csv")

# --- 3. DICCIONARIO Y FUNCIÓN DE REPARACIÓN ROBUSTA DE MOJIBAKE ---
diccionario_mojibake = {
    "Ã³": "ó", "Ã­": "í", "Ã¡": "á", "Ã©": "é", "Ãº": "ú", "Ã±": "ñ",
    "Ã\u0081": "Á", "Ã\u0089": "É", "Ã\u008d": "Í", "Ã\u0083": "Ó", "Ã\u009a": "Ú", "Ã\u0091": "Ñ",
    "Ãa": "ía", "ÃA": "ía", "ã©": "é", "ã±": "ñ", "ã³": "ó", "ã¡": "á", "ã­": "í", "ãº": "ú",
    "CosmÃ©Ticos": "Cosméticos", "Cosmã©Ticos": "Cosméticos", "Ã©Ticos": "éticos"
}

def reparar_cadena(texto):
    if not isinstance(texto, str):
        return texto
    
    # 1. Intentar decodificación binaria si aplica
    try:
        texto_dec = texto.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        texto_dec = texto

    # 2. Reemplazos explícitos de mojibake persistente
    for sucio, limpio in diccionario_mojibake.items():
        texto_dec = texto_dec.replace(sucio, limpio)
        
    return texto_dec.strip()

# --- 4. PROCESAMIENTO Y GENERACIÓN DE BITÁCORA ---
# Guardamos la lista de giros originales
giros_originales = df["nombre_act"].dropna().unique()

bitacora = []
mapa_limpieza = {}

for giro_orig in giros_originales:
    giro_limpio = reparar_cadena(str(giro_orig)).title()
    
    # Corrección fina de tildes/palabras específicas
    giro_limpio = giro_limpio.replace(" De Artículos ", " de Artículos ").replace(" Y ", " y ")
    giro_limpio = giro_limpio.replace(" Publica", " Pública").replace(" Administracion", " Administración")
    
    mapa_limpieza[giro_orig] = giro_limpio
    
    bitacora.append({
        "giro_original": giro_orig,
        "giro_limpio": giro_limpio,
        "hubo_cambio": giro_orig != giro_limpio
    })

df_bitacora = pd.DataFrame(bitacora)

# Identificar cuáles giros limpios resultaron en duplicados fusionados
conteo_limpios = df_bitacora["giro_limpio"].value_counts()
df_bitacora["es_duplicado_fusionado"] = df_bitacora["giro_limpio"].map(lambda x: conteo_limpios[x] > 1)

# Exportar Bitácora
df_bitacora.sort_values(by=["es_duplicado_fusionado", "giro_limpio"], ascending=[False, True], inplace=True)
df_bitacora.to_csv("bitacora_limpieza_giros.csv", index=False, encoding="utf-8-sig")
print("-> Bitácora de limpieza exportada a: bitacora_limpieza_giros.csv")

# --- 5. APLICAR CAMBIOS AL DATASET Y GUARDAR PARQUET ---
df["nombre_act"] = df["nombre_act"].map(mapa_limpieza).fillna(df["nombre_act"])

# Agrupar si existen registros duplicados por municipio, tamaño y giro tras la limpieza
cols_group = [c for c in df.columns if c not in ["total_establecimientos"]]
if "total_establecimientos" in df.columns:
    df = df.groupby(cols_group, as_index=False)["total_establecimientos"].sum()

df.to_parquet(path_parquet, index=False)

print("\n--- 6. RESUMEN EJECUTIVO DE LIMPIEZA ---")
print(f"Giros unicos ANTES: {len(giros_originales):,}")
print(f"Giros unicos DESPUÉS: {df['nombre_act'].nunique():,}")
print(f"Total giros corregidos/modificados: {df_bitacora['hubo_cambio'].sum():,}")
print(f"Total casos con duplicados fusionados: {df_bitacora['es_duplicado_fusionado'].sum():,}")
print("\n¡Proceso completado! Puedes abrir/adjuntar los CSV generados.")