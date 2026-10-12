import duckdb
import os

print("--- 1. INICIANDO CONEXION A DUCKDB ---")

ruta_parquet = "Datos/intermedio/denue_edomex.parquet"
db_path = "data/denue_analitica.duckdb"

os.makedirs("data", exist_ok=True)

if os.path.exists(db_path):
    os.remove(db_path)

con = duckdb.connect(db_path)

print("--- 2. CREANDO TABLA MAESTRA EN BASE DE DATOS LOCAL ---")

con.execute(f"""
CREATE TABLE denue_microdatos AS
SELECT 
    *,
    TRIM(
        REPLACE(
        REPLACE(
        REPLACE(
        REPLACE(
        REPLACE(
        REPLACE(
        REPLACE(
        REPLACE(
        REPLACE(
        REPLACE(
            nombre_act,
            'Ã³', 'ó'),
            'Ã­', 'í'),
            'Ã©', 'é'),
            'Ã¡', 'á'),
            'Ãº', 'ú'),
            'Ã±', 'ñ'),
            'ÃA', 'ía'),
            'ã©', 'é'),
            'ã³', 'ó'),
            'ã¡', 'á')
    ) AS nombre_act_limpio
FROM '{ruta_parquet}'
""")

print("--- 3. CREANDO INDICES ---")
con.execute("CREATE INDEX idx_municipio_giro ON denue_microdatos(municipio, nombre_act_limpio);")

total_filas = con.execute("SELECT COUNT(*) FROM denue_microdatos").fetchone()[0]
giros_unicos = con.execute("SELECT COUNT(DISTINCT nombre_act_limpio) FROM denue_microdatos").fetchone()[0]

print("\n========================================================")
print(f"BASE DE DATOS CREADA EXITOSAMENTE EN: {db_path}")
print(f"Registros totales cargados (microdatos): {total_filas:,}")
print(f"Giros economicos unicos homologados: {giros_unicos:,}")
print("========================================================\n")

df_columnas = con.execute("DESCRIBE denue_microdatos").fetchdf()
df_columnas.to_csv("reporte_estructura_db.csv", index=False)
print("-> Estructura exportada a: reporte_estructura_db.csv")

con.close()
