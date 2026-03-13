

# 🎓 Goit-IA: Asistente Virtual Universitario

Este repositorio contiene el código fuente de **Goit-IA**, un sistema de chatbot híbrido diseñado para la Universidad Veracruzana. El sistema combina técnicas de **RAG (Retrieval-Augmented Generation)** utilizando LangChain y ChromaDB, junto con un sistema de caché semántico basado en **KNN (K-Nearest Neighbors)** para optimizar las respuestas frecuentes.

## 🚀 Características Principales

* **Modelo Híbrido:** Utiliza KNN para respuestas rápidas de preguntas frecuentes y LLM (Groq) para generación de contenido complejo.
* **RAG (Búsqueda Vectorial):** Capacidad de leer y aprender de PDFs y URLs proporcionados.
* **Base de Datos Vectorial:** Implementación con ChromaDB persistente.
* **Embeddings Locales:** Uso de Ollama para la generación de embeddings, garantizando privacidad y eficiencia.
* **Panel de Administración:** Scripts para actualización y reentrenamiento de la base de conocimiento (`admin_db.py`).

---

## 📋 Requisitos Previos

Antes de instalar el proyecto, asegúrate de tener instalado lo siguiente en tu sistema:

1.  **Python 3.10 o superior**
2.  **Git**
3.  **Ollama** (Crucial para el funcionamiento de los embeddings)

---

## 🛠️ Guía de Instalación

Sigue estos pasos para configurar el entorno de desarrollo local:

### 1. Clonar el Repositorio

```bash
git clone <URL_DE_TU_REPOSITORIO>
cd <NOMBRE_DE_LA_CARPETA>
````

### 2\. Crear un Entorno Virtual (Recomendado)

```bash
# En Windows
python -m venv venv
.\venv\Scripts\activate

# En macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3\. Instalar Dependencias de Python

Instala las librerías necesarias listadas en `requirements.txt`:

```bash
pip install -r requirements.txt
```

-----

## 🦙 Configuración de Ollama (IMPORTANTE)

Este sistema utiliza **Ollama** localmente para generar los embeddings de los documentos. Sin este paso, el sistema **no funcionará**.

1.  Descarga e instala Ollama desde [ollama.com](https://ollama.com).
2.  Una vez instalado, abre tu terminal y ejecuta el siguiente comando para descargar el modelo de embeddings específico que utiliza el sistema:

<!-- end list -->

```bash
ollama pull nomic-embed-text
```

> **Nota:** El código está configurado explícitamente para buscar el modelo `nomic-embed-text`. Asegúrate de que la descarga finalice correctamente.

-----

## 🔑 Configuración de Variables de Entorno (.env)

Por razones de seguridad, las claves de API no se incluyen en el repositorio.

⚠️ **Debes solicitar el archivo `.env` al propietario del repositorio.**

Una vez que lo tengas, colócalo en la raíz del proyecto. El archivo debe contener, como mínimo, las siguientes variables:

```env
GROQ_API_KEY=gsk_... (Tu clave de Groq)
SECRET_KEY=... (Clave secreta para sesiones de Flask)
```

*Si no tienes el archivo, el sistema lanzará un error al intentar iniciar.*

-----

## ▶️ Ejecución del Sistema

Una vez configurado todo, puedes iniciar la aplicación Flask:

```bash
python app.py
```

El servidor iniciará generalmente en: `http://localhost:5010` (o la IP indicada en la terminal).

-----
## 📂 Estructura del Proyecto

El sistema está organizado de manera modular para separar la lógica, los modelos y las rutas de la aplicación web:

```text
GOIT-IA/
├── data/                   # Gestión de datos y base vectorial
│   ├── chroma_db_web/      # Base de datos vectorial persistente (ChromaDB)
│   ├── uploads/            # Almacenamiento temporal de PDFs subidos
│   ├── admin_db.py         # Script para procesar documentos y actualizar la DB
│   ├── faq.csv             # Dataset para el modelo KNN
│   └── registry.json       # Registro de fuentes (URLs y PDFs)
│
├── logic/                  # Lógica de negocio
│   └── seleccion_modelo.py # Orquestador (decide entre usar KNN o LLM)
│
├── models/                 # Definición de modelos de IA
│   ├── modelo_knn.py       # Algoritmo de similitud para FAQ
│   └── modelo_llm.py       # Configuración RAG con LangChain y Groq
│
├── routes/                 # Blueprints de Flask (Rutas)
│   ├── app_acercade.py
│   ├── app_admin.py
│   ├── app_chatbot.py
│   ├── app_informacion.py
│   ├── app_inicio.py
│   └── app_privacidad.py
│
├── static/                 # Archivos estáticos
│   ├── css/                # Estilos (chat.css, dashboard.css, etc.)
│   ├── images/             # Recursos gráficos
│   └── js/                 # Scripts del frontend (app.js, theme.js)
│
├── templates/              # Plantillas HTML (Jinja2)
│   ├── admin/              # Vistas de administración
│   ├── base.html           # Layout principal
│   ├── chatbot.html        # Interfaz del chat
│   └── ... (otras vistas)
│
├── app.py                  # Punto de entrada de la aplicación Flask
├── requirements.txt        # Dependencias del proyecto
└── .env                    # Variables de entorno (NO INCLUIDO EN EL REPO)

<!-- end list -->
