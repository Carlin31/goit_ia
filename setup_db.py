# setup_db.py
from database import init_db

if __name__ == "__main__":
    print("🛠️ Iniciando configuración de MongoDB...")
    try:
        init_db()
        print("🚀 MongoDB listo. Ahora puedes ejecutar app.py")
    except Exception as e:
        print(f"❌ Error al inicializar MongoDB: {e}")