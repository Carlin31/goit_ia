import pandas as pd
import os
import sys

# --- 1. CONFIGURACIÓN DE RUTAS E IMPORTACIONES ---
# Obtenemos la ruta donde está este archivo (carpeta 'data')
current_dir = os.path.dirname(os.path.abspath(__file__))
# Obtenemos la ruta padre (carpeta raíz del proyecto)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
# Agregamos la ruta padre al sistema para poder importar 'database'
sys.path.append(parent_dir)

try:
    from database import engine, init_db
    print("✅ Módulo 'database' importado correctamente.")
except ImportError as e:
    print(f"❌ Error crítico importando database: {e}")
    sys.exit(1)

# --- 2. INICIALIZAR BASE DE DATOS ---
print("🔨 Inicializando tablas en Postgres local...")
init_db()

# --- 3. MIGRAR FAQ ---
# Buscamos el archivo csv en el mismo directorio que este script
faq_path = os.path.join(current_dir, 'faq.csv')

if os.path.exists(faq_path):
    print(f"📥 Leyendo FAQ desde: {faq_path}")
    df = pd.read_csv(faq_path)
    
    # Renombrar columnas para coincidir con el modelo
    df.columns = ['pregunta', 'respuesta']
    
    # --- LIMPIEZA DE DATOS (NUEVO) ---
    # Eliminamos filas donde la respuesta sea nula (NaN) para evitar errores SQL
    filas_antes = len(df)
    df = df.dropna(subset=['respuesta'])
    filas_despues = len(df)
    
    if filas_antes > filas_despues:
        print(f"⚠️ Se eliminaron {filas_antes - filas_despues} filas vacías o corruptas.")
    
    # Insertar en la base de datos
    df.to_sql('faq', engine, if_exists='append', index=False)
    print("✅ FAQ migrado exitosamente.")
else:
    print(f"❌ No se encontró el archivo: {faq_path}")

# --- 4. MIGRAR LOGS ---
log_path = os.path.join(current_dir, 'access_log.csv')

if os.path.exists(log_path):
    print(f"📥 Leyendo Logs desde: {log_path}")
    df = pd.read_csv(log_path)
    
    # Ajustar nombres de columnas
    df.columns = ['dia', 'fecha', 'hora', 'programa', 'dispositivo', 'ip']
    
    # Opcional: Limpieza básica para logs si fuera necesaria
    # df = df.dropna() 
    
    df.to_sql('access_log', engine, if_exists='append', index=False)
    print("✅ Logs migrados exitosamente.")
else:
    print(f"❌ No se encontró el archivo: {log_path}")