from pdfminer.high_level import extract_text
import fitz  # PyMuPDF


def get_pdf_file_contents(pdf_filepath: str):
    file_contents = None
    with open(pdf_filepath, 'r') as f_obj:
        file_contents = f_obj.read()
    return file_contents


def parse_pdf_with_pdfminer(pdf_path):
    text = extract_text(pdf_path)
    return text


def parse_pdf_with_pymupdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text += page.get_text()

    doc.close()
    return text
