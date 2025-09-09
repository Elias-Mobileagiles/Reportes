import PyPDF2
import difflib
import os
import sys
import re # Importar para expresiones regulares
from datetime import datetime

def extract_text_from_pdf(pdf_path):
    """
    Extrae todo el texto de un archivo PDF.

    Args:
        pdf_path (str): La ruta al archivo PDF.

    Returns:
        str: El texto extraído del PDF.
    """
    text = ""
    try:
        if not os.path.exists(pdf_path):
            print(f"ERROR: El archivo no existe en la ruta: '{pdf_path}'")
            return None

        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            if reader.is_encrypted:
                print(f"ADVERTENCIA: El PDF '{pdf_path}' está encriptado. Intentando desencriptar sin contraseña...")
                # Si tienes una contraseña, podrías usar: reader.decrypt('tu_contrasena_aqui')

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                else:
                    print(f"ADVERTENCIA: Página {page_num+1} de '{pdf_path}' no contiene texto extraíble o es una imagen escaneada.")
            
            if not text.strip():
                print(f"ADVERTENCIA: No se pudo extraer texto significativo de '{pdf_path}'. Podría ser un PDF escaneado o vacío.")

    except PyPDF2.errors.PdfReadError as e:
        print(f"ERROR PyPDF2 al leer '{pdf_path}': {e}. El archivo podría estar corrupto o no ser un PDF válido.")
        return None
    except FileNotFoundError:
        print(f"ERROR: El archivo no fue encontrado en '{pdf_path}'.")
        return None
    except Exception as e:
        print(f"ERROR inesperado al procesar '{pdf_path}': {e}")
        return None
    return text

def compare_pdf_texts(pdf1_path, pdf2_path):
    """
    Compara el texto de dos archivos PDF y devuelve las diferencias.

    Args:
        pdf1_path (str): La ruta al primer archivo PDF.
        pdf2_path (str): La ruta al segundo archivo PDF.

    Returns:
        list: Una lista de cadenas que representan las diferencias,
              o None si hubo un error al extraer el texto.
    """
    print(f"Extrayendo texto de: {pdf1_path}")
    text1 = extract_text_from_pdf(pdf1_path)
    if text1 is None:
        return None

    print(f"Extrayendo texto de: {pdf2_path}")
    text2 = extract_text_from_pdf(pdf2_path)
    if text2 is None:
        return None

    # Dividir el texto en líneas para la comparación
    lines1 = text1.splitlines(keepends=True)
    lines2 = text2.splitlines(keepends=True)

    # Llamar directamente a difflib.unified_diff
    diff = difflib.unified_diff(lines1, lines2, fromfile=os.path.basename(pdf1_path), tofile=os.path.basename(pdf2_path))
    
    return list(diff)

def get_pdfs_by_date(directory_path, filename_pattern=r'Audit_aru_(\d{4}-\d{2}-\d{2})\.pdf'):
    """
    Encuentra los dos archivos PDF más recientes en un directorio
    basándose en la fecha incrustada en el nombre del archivo.

    Args:
        directory_path (str): La ruta al directorio donde buscar los PDFs.
        filename_pattern (str): Expresión regular para extraer la fecha del nombre del archivo.
                                 Debe tener un grupo de captura para la fecha.

    Returns:
        tuple: Una tupla (ruta_pdf_antiguo, ruta_pdf_reciente) de los dos archivos más recientes,
               o (None, None) si no se encuentran suficientes archivos.
    """
    pdf_files_with_dates = []
    date_format = "%Y-%m-%d"

    if not os.path.isdir(directory_path):
        print(f"ERROR: El directorio '{directory_path}' no existe o no es un directorio válido.")
        return None, None

    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            match = re.search(filename_pattern, filename)
            if match:
                date_str = match.group(1)
                try:
                    file_date = datetime.strptime(date_str, date_format)
                    pdf_files_with_dates.append((file_date, os.path.join(directory_path, filename)))
                except ValueError:
                    print(f"ADVERTENCIA: No se pudo parsear la fecha '{date_str}' de '{filename}'. Saltando.")
            else:
                print(f"ADVERTENCIA: El archivo '{filename}' no coincide con el patrón de nombre esperado. Saltando.")

    # Ordenar los archivos por fecha, del más antiguo al más reciente
    pdf_files_with_dates.sort(key=lambda x: x[0])

    if len(pdf_files_with_dates) < 2:
        print(f"ERROR: Se necesitan al menos 2 archivos PDF con el patrón '{filename_pattern}' en '{directory_path}' para comparar.")
        return None, None
    
    # Tomar los dos últimos, que serán los dos más recientes
    oldest_recent_pdf = pdf_files_with_dates[-2][1] # El penúltimo es el más antiguo de los dos más recientes
    newest_pdf = pdf_files_with_dates[-1][1]       # El último es el más reciente

    return oldest_recent_pdf, newest_pdf

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python compare_pdfs.py <ruta_al_directorio_de_pdfs>")
        sys.exit(1)

    pdf_directory = sys.argv[1]

    print(f"\n--- Buscando PDFs en: {pdf_directory} ---")
    pdf_path1, pdf_path2 = get_pdfs_by_date(pdf_directory)

    if pdf_path1 is None or pdf_path2 is None:
        print("No se pudo obtener los archivos PDF para la comparación. Saliendo.")
        sys.exit(1)

    print(f"Archivos seleccionados para comparación:")
    print(f"  Antiguo (Base): {os.path.basename(pdf_path1)}")
    print(f"  Reciente (Nuevo): {os.path.basename(pdf_path2)}")

    print("\n--- Iniciando comparación de PDFs ---")
    differences = compare_pdf_texts(pdf_path1, pdf_path2)

    if differences is not None:
        if len(differences) > 0:
            print("\n--- Diferencias encontradas: ---")
            for line in differences:
                print(line, end='')
            sys.exit(2) # Exit with a different code to indicate differences were found
        else:
            print("\nLos archivos PDF son idénticos en su contenido de texto.")
            sys.exit(0) # Exit with success code
    else:
        print("\nNo se pudo realizar la comparación debido a errores en la extracción de texto de uno o ambos archivos.")
        sys.exit(1) # Exit with an error code