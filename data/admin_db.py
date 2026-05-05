import os
import time
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN ---
CURRENT_FILE_PATH = os.path.abspath(__file__)
DATA_DIR = os.path.dirname(CURRENT_FILE_PATH)
PROJECT_ROOT = os.path.dirname(DATA_DIR)

MODELO_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
HF_TOKEN = os.getenv("HF_TOKEN")
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT = os.getenv("CHROMA_TENANT")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE")
CHROMA_COLLECTION = "goit_vectores"

# chunk_size=1800 y overlap=150 equilibra calidad de recuperación con cantidad de fragmentos.
# CHROMA_MAX_RECORDS debe mantenerse por debajo del límite del plan (300 en plan gratuito).
CHUNK_SIZE = 1800
CHUNK_OVERLAP = 150
CHROMA_MAX_RECORDS = 280  # margen de seguridad antes del límite de 300


def actualizar_base_datos_completa(registry_data):
    """
    Función Generadora (Streaming) para entrenar la IA.
    Guarda los vectores en Chroma Cloud — sin almacenamiento local.

    Optimizaciones aplicadas:
    - chunk_size=1000 (reducido de 2500): fragmentos más granulares para recuperación precisa.
    - chunk_overlap=200 (aumentado de 50): mejor continuidad de contexto entre fragmentos.
    - Metadata de fuente en cada fragmento: permite filtrado futuro por origen.
    """

    def enviar_msg(texto):
        print(f"[IA TRAIN] {texto}")
        texto_seguro = texto.replace('\n', ' ')
        return f"data: {texto_seguro}\n\n"

    try:
        yield enviar_msg("🚀 Iniciando proceso de entrenamiento...")

        todos_los_documentos = []

        # --- A) Procesar URLs ---
        urls = [item['url'] for item in registry_data.get('urls', [])]
        if urls:
            yield enviar_msg(f"📡 Descargando {len(urls)} URLs...")
            for url_item in registry_data.get('urls', []):
                url = url_item['url']
                nombre = url_item.get('name', url)
                try:
                    loader_web = WebBaseLoader([url])
                    docs_web = loader_web.load()
                    # Agregar metadata de fuente a cada documento
                    for doc in docs_web:
                        doc.metadata['fuente'] = nombre
                        doc.metadata['tipo'] = 'url'
                    todos_los_documentos.extend(docs_web)
                    yield enviar_msg(f"  ✅ {nombre}: {len(docs_web)} página(s) descargadas.")
                except Exception as e:
                    yield enviar_msg(f"  ⚠️ Error en '{nombre}': {str(e)}")

            yield enviar_msg(f"📊 Total desde URLs: {sum(1 for d in todos_los_documentos if d.metadata.get('tipo') == 'url')} páginas.")

        # --- B) Procesar PDFs ---
        pdfs = registry_data.get('pdfs', [])
        if pdfs:
            yield enviar_msg(f"📂 Detectados {len(pdfs)} PDFs en registro.")
            count_pdf = 0

            for pdf_item in pdfs:
                rel_path = pdf_item.get('path')
                abs_path = os.path.join(PROJECT_ROOT, rel_path)

                if os.path.exists(abs_path):
                    yield enviar_msg(f"📄 Procesando: {pdf_item['filename']}...")
                    try:
                        loader_pdf = PyPDFLoader(abs_path)
                        docs_pdf = loader_pdf.load()
                        # Agregar metadata de fuente a cada página
                        for doc in docs_pdf:
                            doc.metadata['fuente'] = pdf_item['filename']
                            doc.metadata['tipo'] = 'pdf'
                        todos_los_documentos.extend(docs_pdf)
                        count_pdf += 1
                        yield enviar_msg(f"  ✅ {pdf_item['filename']}: {len(docs_pdf)} página(s).")
                    except Exception as e:
                        yield enviar_msg(f"  ⚠️ Fallo al leer PDF: {e}")
                else:
                    yield enviar_msg(f"⚠️ Archivo no encontrado: {rel_path}")
                    print(f"DEBUG: Busqué en -> {abs_path}")

            yield enviar_msg(f"✅ {count_pdf}/{len(pdfs)} PDFs procesados.")

        # --- C) Fragmentar y cargar en Chroma Cloud ---
        if todos_los_documentos:
            yield enviar_msg(f"✂️ Fragmentando {len(todos_los_documentos)} documentos...")
            yield enviar_msg(f"   chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = text_splitter.split_documents(todos_los_documentos)
            yield enviar_msg(f"📊 Total de fragmentos generados: {len(chunks)}")

            # Salvaguarda de cuota: Chroma Cloud limita el número de registros por plan.
            if len(chunks) > CHROMA_MAX_RECORDS:
                yield enviar_msg(
                    f"⚠️ Se generaron {len(chunks)} fragmentos, pero el límite configurado "
                    f"es {CHROMA_MAX_RECORDS}. Se usarán solo los primeros {CHROMA_MAX_RECORDS} "
                    f"fragmentos para no exceder la cuota de Chroma Cloud."
                )
                yield enviar_msg(
                    "   Consejo: reduce la cantidad de documentos, o solicita un aumento de cuota "
                    "en trychroma.com para procesar todos los fragmentos."
                )
                chunks = chunks[:CHROMA_MAX_RECORDS]
                yield enviar_msg(f"✂️ Fragmentos reducidos a {len(chunks)}.")

            yield enviar_msg("☁️ Conectando con Chroma Cloud...")
            chroma_client = chromadb.CloudClient(
                api_key=CHROMA_API_KEY,
                tenant=CHROMA_TENANT,
                database=CHROMA_DATABASE
            )

            yield enviar_msg("🔄 Conectando con API de embeddings (HuggingFace)...")
            embedding_function = HuggingFaceEndpointEmbeddings(
                model=MODELO_EMBEDDING,
                huggingfacehub_api_token=HF_TOKEN
            )

            # Limpiar colección anterior si existe
            colecciones = [c.name for c in chroma_client.list_collections()]
            if CHROMA_COLLECTION in colecciones:
                yield enviar_msg("🧹 Limpiando colección anterior en Chroma Cloud...")
                chroma_client.delete_collection(CHROMA_COLLECTION)

            # Crear colección nueva y cargar vectores
            yield enviar_msg("💾 Insertando vectores en Chroma Cloud...")
            vector_db = Chroma(
                client=chroma_client,
                collection_name=CHROMA_COLLECTION,
                embedding_function=embedding_function
            )
            vector_db.add_documents(documents=chunks)

            yield enviar_msg("✅ ¡Entrenamiento exitoso! Vectores guardados en Chroma Cloud.")
            yield enviar_msg(f"   {len(chunks)} fragmentos listos para recuperación precisa.")
        else:
            yield enviar_msg("⚠️ No se encontraron documentos válidos (ni URLs ni PDFs).")

    except Exception as e:
        import traceback
        traceback.print_exc()
        yield enviar_msg(f"❌ ERROR CRÍTICO DEL SISTEMA: {str(e)}")

    finally:
        time.sleep(1)
        yield "event: close\ndata: close\n\n"
