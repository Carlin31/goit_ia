import os
import re
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

def limpiar_texto(texto):
    """
    Elimina caracteres extraños, espacios múltiples y normaliza el texto.
    """
    if not texto:
        return ""
    
    # 1. Reemplazar múltiples saltos de línea por uno solo
    texto = re.sub(r'\n+', '\n', texto)
    # 2. Reemplazar múltiples espacios por uno solo
    texto = re.sub(r'\s+', ' ', texto)
    # 3. Eliminar caracteres no imprimibles (opcional, según necesidad)
    # texto = re.sub(r'[^\x00-\x7F]+', ' ', texto) 
    
    return texto.strip()

def procesar_y_limpiar_pdf(ruta_entrada, ruta_salida):
    """
    Lee un PDF sucio, extrae su texto, lo limpia y genera un 
    NUEVO PDF estandarizado solo con texto.
    """
    try:
        reader = PdfReader(ruta_entrada)
        buffer_texto = []

        # --- FASE 1: Extracción y Limpieza ---
        for page in reader.pages:
            texto_crudo = page.extract_text()
            if texto_crudo:
                texto_limpio = limpiar_texto(texto_crudo)
                buffer_texto.append(texto_limpio)
        
        full_text = "\n\n".join(buffer_texto)

        # --- FASE 2: Generación de PDF Nuevo (ReportLab) ---
        c = canvas.Canvas(ruta_salida, pagesize=A4)
        width, height = A4
        text_object = c.beginText()
        
        # Configuración de márgenes y fuente
        margin = 1 * inch
        text_object.setTextOrigin(margin, height - margin)
        text_object.setFont("Helvetica", 10)
        
        # Escribir el texto línea por línea respetando el ancho
        # (Lógica simple de ajuste de línea)
        max_width = width - (2 * margin)
        
        palabras = full_text.split(' ')
        linea_actual = ""
        
        for palabra in palabras:
            # Intentamos agregar una palabra
            test_line = linea_actual + palabra + " "
            if c.stringWidth(test_line, "Helvetica", 10) < max_width:
                linea_actual = test_line
            else:
                # La línea está llena, la escribimos
                text_object.textLine(linea_actual)
                
                # Verificamos si llegamos al final de la página
                if text_object.getY() < margin:
                    c.drawText(text_object)
                    c.showPage() # Nueva página
                    text_object = c.beginText()
                    text_object.setTextOrigin(margin, height - margin)
                    text_object.setFont("Helvetica", 10)
                
                linea_actual = palabra + " "
        
        # Escribir la última línea pendiente
        if linea_actual:
            text_object.textLine(linea_actual)
            
        c.drawText(text_object)
        c.save()
        
        return True, "PDF Limpio generado correctamente."

    except Exception as e:
        return False, f"Error en limpieza: {str(e)}"