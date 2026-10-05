import os
import zipfile

# Rutas del proyecto
ruta_datos = "Datos"
carpeta_conjunto = os.path.join(ruta_datos, "conjunto_de_datos")
carpeta_diccionario = os.path.join(ruta_datos, "diccionario")
carpeta_metadatos = os.path.join(ruta_datos, "metadatos")

# Buscar todos los archivos .zip que terminen en _csv
zips = [f for f in os.listdir(ruta_datos) if f.endswith('_csv.zip') or f.endswith('_csv')]

print(f"Encontrados {len(zips)} archivos ZIP de datos CSV. Iniciando extracción automática...\n")

for i, zip_name in enumerate(zips, start=1):
    ruta_zip = os.path.join(ruta_datos, zip_name)
    
    # Si Windows lo descargó como carpeta comprimida o zip
    if os.path.isfile(ruta_zip) and zip_name.endswith('.zip'):
        try:
            with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    filename = file_info.filename
                    
                    # Ignoramos carpetas internas vacías
                    if file_info.is_dir():
                        continue
                    
                    # 1. Archivo principal de comercios -> conjunto_de_datos
                    if "conjunto_de_datos" in filename and filename.endswith('.csv'):
                        file_info.filename = f"denue_part_{i}.csv"
                        zip_ref.extract(file_info, carpeta_conjunto)
                        print(f"[{i}/{len(zips)}] Extraído conjunto de datos -> {file_info.filename}")
                        
                    # 2. Diccionario de datos -> diccionario
                    elif "diccionario_de_datos" in filename and filename.endswith('.csv'):
                        file_info.filename = f"diccionario_part_{i}.csv"
                        zip_ref.extract(file_info, carpeta_diccionario)
                        print(f"   └── Extraído diccionario")
                        
                    # 3. Metadatos -> metadatos
                    elif "metadatos" in filename:
                        file_info.filename = f"metadatos_part_{i}.txt"
                        zip_ref.extract(file_info, carpeta_metadatos)
                        print(f"   └── Extraído metadatos")
        except Exception as e:
            print(f"Error procesando {zip_name}: {e}")

print("\n==========================================")
print("¡Proceso completado con éxito! Todos los datos están organizados.")
print("==========================================")