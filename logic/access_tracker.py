import pandas as pd
from datetime import datetime
import sys
import os

# --- CONFIGURACIÓN DE RUTAS ---
current_dir  = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)

# --- IMPORTS DE BASE DE DATOS (MongoDB) ---
from database import (
    insert_access_log, get_all_access_logs,
    insert_chat_log,
)


# ──────────────────────────────────────────────────────────────
# REGISTRO DE ACCESO  (paso del modal: matrícula + programa)
# ──────────────────────────────────────────────────────────────

def registrar_acceso(programa: str, ip: str,
                     dispositivo: str, matricula: str = "") -> bool:
    """
    Guarda el registro de acceso en MongoDB.
    El campo `matricula` es opcional para compatibilidad con registros
    anteriores que no lo incluyen.
    """
    ahora = datetime.now()
    try:
        insert_access_log(
            dia        = ahora.strftime('%A'),
            fecha      = ahora.strftime('%Y-%m-%d'),
            hora       = ahora.strftime('%H:%M:%S'),
            programa   = programa,
            dispositivo= dispositivo,
            ip         = ip,
            matricula  = matricula,
        )
        print(f"✅ Acceso registrado: {matricula} | {programa} desde {ip}")
        return True
    except Exception as e:
        print(f"❌ Error registrando acceso en MongoDB: {e}")
        return False


# ──────────────────────────────────────────────────────────────
# REGISTRO DE PREGUNTA  (nuevo — por cada mensaje al chat)
# ──────────────────────────────────────────────────────────────

def registrar_pregunta(matricula: str, programa: str,
                       pregunta: str, respuesta: str,
                       modelo: str) -> bool:
    """
    Guarda cada pregunta/respuesta junto con la matrícula del alumno,
    el programa educativo y el modelo que respondió (KNN o LLM).
    """
    ahora = datetime.now()
    try:
        insert_chat_log(
            matricula = matricula,
            programa  = programa,
            pregunta  = pregunta,
            respuesta = respuesta,
            modelo    = modelo,
            fecha     = ahora.strftime('%Y-%m-%d'),
            hora      = ahora.strftime('%H:%M:%S'),
        )
        print(f"✅ Pregunta registrada: {matricula} | modelo={modelo}")
        return True
    except Exception as e:
        print(f"❌ Error registrando pregunta en MongoDB: {e}")
        return False


# ──────────────────────────────────────────────────────────────
# ESTADÍSTICAS Y LISTADOS  (para el panel de admin)
# ──────────────────────────────────────────────────────────────

def obtener_estadisticas_diarias() -> dict:
    """Conteo de accesos por programa (para tarjetas del dashboard)."""
    try:
        registros = get_all_access_logs()
        if not registros:
            return {}
        df = pd.DataFrame(registros)
        return df['programa'].value_counts().to_dict()
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return {}


def obtener_todos_los_registros() -> list[dict]:
    """
    Todos los registros de acceso para la tabla del panel de administración,
    del más reciente al más antiguo.
    """
    try:
        registros = get_all_access_logs()
        if not registros:
            return []

        df = pd.DataFrame(registros)

        # Asegurar que la columna matricula exista (registros viejos no la tienen)
        if 'matricula' not in df.columns:
            df['matricula'] = ''

        df = df.fillna('')
        df = df.sort_values(by=['fecha', 'hora'], ascending=False)
        return df.to_dict(orient='records')

    except Exception as e:
        print(f"❌ Error obteniendo registros históricos: {e}")
        return []
