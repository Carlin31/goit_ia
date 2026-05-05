import pandas as pd
from datetime import datetime
import sys
import os

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)

# --- IMPORTS DE BASE DE DATOS (MongoDB) ---
from database import insert_access_log, get_all_access_logs


def registrar_acceso(programa, ip, dispositivo):
    """
    Guarda el registro de acceso en MongoDB.
    """
    ahora = datetime.now()

    try:
        insert_access_log(
            dia=ahora.strftime('%A'),
            fecha=ahora.strftime('%Y-%m-%d'),
            hora=ahora.strftime('%H:%M:%S'),
            programa=programa,
            dispositivo=dispositivo,
            ip=ip
        )
        print(f"✅ Acceso registrado en MongoDB: {programa} desde {ip}")
        return True

    except Exception as e:
        print(f"❌ Error registrando acceso en MongoDB: {e}")
        return False


def obtener_estadisticas_diarias():
    """
    Devuelve el conteo de visitas por programa para las gráficas.
    """
    try:
        registros = get_all_access_logs()

        if not registros:
            return {}

        df = pd.DataFrame(registros)
        return df['programa'].value_counts().to_dict()

    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return {}


def obtener_todos_los_registros():
    """
    Devuelve todos los registros para la tabla del panel de administración,
    ordenados del más reciente al más antiguo.
    """
    try:
        registros = get_all_access_logs()

        if not registros:
            return []

        df = pd.DataFrame(registros)

        # Ordenar por fecha y hora descendente
        df = df.sort_values(by=['fecha', 'hora'], ascending=False)

        return df.to_dict(orient='records')

    except Exception as e:
        print(f"❌ Error obteniendo registros históricos: {e}")
        return []