# migrate_postgres_to_mongo.py
"""
Script de migración única: copia los datos de PostgreSQL a MongoDB.
Ejecutar UNA sola vez antes de cambiar a la nueva versión del proyecto.

Uso:
    python migrate_postgres_to_mongo.py
"""

import os
import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# --- CONEXIÓN POSTGRESQL (origen) ---
PG_URL = os.getenv("DATABASE_URL")  # tu .env anterior

# --- CONEXIÓN MONGODB (destino) ---
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "goit_local")


def migrar():
    print("🔄 Conectando a PostgreSQL...")
    pg_conn = psycopg2.connect(PG_URL)
    cursor = pg_conn.cursor()

    print("🔄 Conectando a MongoDB...")
    mongo_client = MongoClient(MONGO_URL)
    mongo_db = mongo_client[DB_NAME]

    # --- MIGRAR TABLA faq ---
    print("\n📋 Migrando tabla FAQ...")
    cursor.execute("SELECT id, pregunta, respuesta FROM faq")
    faq_rows = cursor.fetchall()

    if faq_rows:
        faq_docs = [
            {"pregunta": row[1], "respuesta": row[2]}
            for row in faq_rows
        ]
        mongo_db["faq"].delete_many({})  # limpia antes de insertar
        mongo_db["faq"].insert_many(faq_docs)
        print(f"   ✅ {len(faq_docs)} registros FAQ migrados.")
    else:
        print("   ⚠️  Tabla FAQ vacía, nada que migrar.")

    # --- MIGRAR TABLA access_log ---
    print("\n📋 Migrando tabla access_log...")
    cursor.execute("SELECT id, dia, fecha, hora, programa, dispositivo, ip FROM access_log")
    log_rows = cursor.fetchall()

    if log_rows:
        log_docs = [
            {
                "dia": row[1],
                "fecha": row[2],
                "hora": row[3],
                "programa": row[4],
                "dispositivo": row[5],
                "ip": row[6],
            }
            for row in log_rows
        ]
        mongo_db["access_log"].delete_many({})
        mongo_db["access_log"].insert_many(log_docs)
        print(f"   ✅ {len(log_docs)} registros access_log migrados.")
    else:
        print("   ⚠️  Tabla access_log vacía, nada que migrar.")

    # --- CIERRE ---
    cursor.close()
    pg_conn.close()
    mongo_client.close()
    print("\n🚀 Migración completada exitosamente.")


if __name__ == "__main__":
    if not PG_URL:
        print("❌ Define DATABASE_URL en tu .env para conectar a PostgreSQL.")
    else:
        migrar()