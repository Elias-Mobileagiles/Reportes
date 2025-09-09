import PyPDF2
import difflib
import os
import sys # Import the sys module

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
    diff = difflib.unified_diff(lines1, lines2, fromfile=pdf1_path, tofile=pdf2_path)
    
    return list(diff)

if __name__ == "__main__":
    # --- Check for command-line arguments ---
    if len(sys.argv) != 3:
        print("Uso: python compare_pdfs.py <ruta_pdf1> <ruta_pdf2>")
        sys.exit(1) # Exit with an error code

    pdf_path1 = sys.argv[1]
    pdf_path2 = sys.argv[2]

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
        sys.exit(1) # Exit with an error code3.