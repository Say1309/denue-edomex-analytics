import os
import zipfile

ruta_datos = "Datos"
carpeta_conjunto = os.path.join(ruta_datos, "conjunto_de_datos")
carpeta_diccionario = os.path.join(ruta_datos, "diccionario")
carpeta_metadatos = os.path.join(ruta_datos, "metadatos")

# Crear carpetas si no existen
for folder in [carpeta_conjunto, carpeta_diccionario, carpeta_metadatos]:
    os.makedirs(folder, exist_ok=True)

# Buscar todos los .zip en la carpeta Datos
zips = sorted([f for f in os.listdir(ruta_datos) if f.endswith('.zip') or '_csv' in f])

print(f"Total de archivos ZIP/Comprimidos detectados: {len(zips)}\n")

exitosos = 0
saltados = []

for i, zip_name in enumerate(zips, start=1):
    ruta_zip = os.path.join(ruta_datos, zip_name)
    
    if os.path.isfile(ruta_zip) and zip_name.endswith('.zip'):
        try:
            with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
                archivos_internos = zip_ref.namelist()
                
                # Buscar cualquier CSV masivo dentro del zip (sin importar subcarpeta)
                csv_masivos = [f for f in archivos_internos if f.endswith('.csv') and 'diccionario' not in f.lower()]
                diccionarios = [f for f in archivos_internos if f.endswith('.csv') and 'diccionario' in f.lower()]
                txt_metadatos = [f for f in archivos_internos if f.endswith('.txt')]
                
                if csv_masivos:
                    # Extraer el CSV masivo principal
                    archivo_csv = csv_masivos[0]
                    zip_ref.extract(archivo_csv, carpeta_conjunto)
                    
                    # Renombrar para evitar sobreescrituras
                    nombre_origen = os.path.join(carpeta_conjunto, archivo_csv)
                    nombre_destino = os.path.join(carpeta_conjunto, f"denue_part_{i}.csv")
                    
                    # Si estaba dentro de subcarpetas, moverlo a la raíz de conjunto_de_datos
                    if os.path.exists(nombre_origen):
                        os.replace(nombre_origen, nombre_destino)
                    
                    exitosos += 1
                    print(f"[{i}/{len(zips)}] Extraído exitosamente -> denue_part_{i}.csv")
                else:
                    saltados.append((zip_name, "No se encontró archivo .csv de datos dentro"))
                    
        except Exception as e:
            saltados.append((zip_name, f"Error al abrir ZIP: {e}"))

print("\n==========================================")
print(f" RESUMEN DE AUDITORÍA:")
print(f" Archivos procesados con éxito: {exitosos}/{len(zips)}")
print(f" Archivos saltados/con advertencia: {len(saltados)}")
print("==========================================")

if saltados:
    print("\nDetalle de los archivos que no se extrajeron:")
    for zip_n, razon in saltados:
        print(f" ❌ {zip_n} --> Razón: {razon}")