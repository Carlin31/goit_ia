import os
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

# --- CONFIGURACIÃ“N ---
# Calculamos rutas absolutas basadas en la ubicaciÃ³n de este archivo (admin_db.py)
CURRENT_FILE_PATH = os.path.abspath(__file__)
DATA_DIR = os.path.dirname(CURRENT_FILE_PATH)       # Carpeta /data
PROJECT_ROOT = os.path.dirname(DATA_DIR)            # Carpeta RaÃ­z del proyecto
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_db_web")

MODELO_EMBEDDING = "nomic-embed-text"

def actualizar_base_datos_completa(registry_data):
    """
    FunciÃ³n Generadora (Streaming) para entrenar la IA.
    Maneja rutas absolutas para evitar errores de 'Archivo no encontrado'.
    """
    
    # FunciÃ³n auxiliar para formatear mensajes SSE
    def enviar_msg(texto):
        print(f"[IA TRAIN] {texto}") # Log en consola del servidor
        texto_seguro = texto.replace('\n', ' ')
        return f"data: {texto_seguro}\n\n"

    try:
        yield enviar_msg("ðŸš€ Iniciando proceso de entrenamiento...")
        
        # 1. Preparar Documentos
        todos_los_documentos = []
        
        # --- A) Procesar URLs ---
        urls = [item['url'] for item in registry_data.get('urls', [])]
        if urls:
            yield enviar_msg(f"ðŸ“¡ Descargando {len(urls)} URLs...")
            try:
                loader_web = WebBaseLoader(urls)
                docs_web = loader_web.load()
                todos_los_documentos.extend(docs_web)
                yield enviar_msg(f"âœ… Descarga web completada: {len(docs_web)} pÃ¡ginas.")
            except Exception as e:
                yield enviar_msg(f"âš ï¸ Error parcial en URLs: {str(e)}")

        # --- B) Procesar PDFs ---
        pdfs = registry_data.get('pdfs', [])
        if pdfs:
            yield enviar_msg(f"ðŸ“‚ Detectados {len(pdfs)} PDFs en registro.")
            count_pdf = 0
            
            for pdf_item in pdfs:
                # Obtenemos la ruta relativa del JSON (ej: data/uploads/doc.pdf)
                rel_path = pdf_item.get('path')
                
                # CONSTRUCCIÃ“N DE RUTA ABSOLUTA (La soluciÃ³n al problema)
                # Unimos la raÃ­z del proyecto con la ruta relativa
                abs_path = os.path.join(PROJECT_ROOT, rel_path)
                
                # Verificamos si existe usando la ruta absoluta
                if os.path.exists(abs_path):
                    yield enviar_msg(f"ðŸ“„ Procesando: {pdf_item['filename']}...")
                    try:
                        loader_pdf = PyPDFLoader(abs_path)
                        docs_pdf = loader_pdf.load()
                        todos_los_documentos.extend(docs_pdf)
                        count_pdf += 1
                    except Exception as e:
                        yield enviar_msg(f"âš ï¸ Fallo al leer PDF (Posible error de formato o librerÃ­a pypdf): {e}")
                else:
                    # Debug: mostramos dÃ³nde intentÃ³ buscar
                    yield enviar_msg(f"âš ï¸ Archivo no encontrado: {rel_path}")
                    print(f"DEBUG: BusquÃ© en -> {abs_path}")

            yield enviar_msg(f"âœ… {count_pdf} PDFs procesados correctamente.")

        # 2. Actualizar ChromaDB
        if todos_los_documentos:
            yield enviar_msg(f"ðŸ”ª Fragmentando {len(todos_los_documentos)} documentos...")
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(todos_los_documentos)
            yield enviar_msg(f"ðŸ“Š Total de fragmentos generados: {len(chunks)}")

            yield enviar_msg("ðŸ”„ Inicializando embeddings (esto puede tardar)...")
            
            embedding_function = OllamaEmbeddings(model=MODELO_EMBEDDING)
            
            # Inicializar Chroma con persistencia
            vector_db = Chroma(
                persist_directory=CHROMA_PATH,
                embedding_function=embedding_function
            )
            
            # Borrado de datos antiguos para evitar duplicados
            ids_actuales = vector_db.get()['ids']
            if ids_actuales:
                yield enviar_msg(f"ðŸ§¹ Limpiando {len(ids_actuales)} registros previos...")
                batch = 5000 
                for i in range(0, len(ids_actuales), batch):
                    vector_db.delete(ids_actuales[i:i+batch])
                    yield enviar_msg(f"   ...Lote {i} borrado.")
            
            yield enviar_msg("ðŸ’¾ Insertando nuevos vectores en ChromaDB...")
            vector_db.add_documents(documents=chunks)
            
            yield enviar_msg("âœ… Â¡Entrenamiento exitoso! Base de datos actualizada.")
        else:
            yield enviar_msg("âš ï¸ No se encontraron documentos vÃ¡lidos (ni URLs ni PDFs funcionales).")

    except Exception as e:
        import traceback
        traceback.print_exc()
        yield enviar_msg(f"âŒ ERROR CRÃTICO DEL SISTEMA: {str(e)}")
        
    finally:
        # FinalizaciÃ³n segura para cerrar el EventSource en JS
        time.sleep(1)
        yield "event: close\ndata: close\n\n"