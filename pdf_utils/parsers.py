from pathlib import Path

from pdf2image import convert_from_path
from pdfminer.high_level import extract_text
import fitz  # PyMuPDF
import os
import json
import pytesseract

from common.utils import get_file_hash, singleton, get_hash_from_string, read_txt_file
from settings import get_tmp_dir


@singleton
class PdfParseManager:

    PARSER_OUTPUT_DIR = f"{get_tmp_dir()}/_PdfParseManager"
    MAPPING_TABLE_FILE_PATH = f"{PARSER_OUTPUT_DIR}/__PDF_MAPPING_TABLE.json"
    PDF_IMAGE_AS_TXT_FILES_DIR_PATH = f"{PARSER_OUTPUT_DIR}/pdf_image_as_txt_files"

    def __init__(self):
        self.mapping_table = {}
        self.bootstrap()

    def _save_mapping_table(self):
        with open(self.MAPPING_TABLE_FILE_PATH, "w") as f_obj:
            json.dump(self.mapping_table, f_obj, indent=4)

    def bootstrap(self):
        os.makedirs(self.PARSER_OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.PDF_IMAGE_AS_TXT_FILES_DIR_PATH, exist_ok=True)
        self.load_pdf_mapping_table()

    def load_pdf_mapping_table(self):
        if os.path.exists(self.MAPPING_TABLE_FILE_PATH):
            with open(self.MAPPING_TABLE_FILE_PATH, "r") as f_obj:
                self.mapping_table = json.load(f_obj)
        else:
            with open(self.MAPPING_TABLE_FILE_PATH, "w") as f_obj:
                f_obj.write("{}")

    def add_pdf_image_to_mapping_table(self, pdf_file_path: str, pdf_file_contents: str):
        pdf_file_hash = get_file_hash(pdf_file_path)
        pdf_file_contents_hash = get_hash_from_string(pdf_file_contents)
        pdf_file_basename = Path(pdf_file_path).stem
        pdf_file_as_txt_file_path = f"{self.PDF_IMAGE_AS_TXT_FILES_DIR_PATH}/{pdf_file_basename}.txt"
        with open(pdf_file_as_txt_file_path, "w") as f_obj:
            f_obj.write(pdf_file_contents)
        self.mapping_table[pdf_file_path] = {
            "pdf_file_hash": pdf_file_hash,
            "pdf_file_contents_hash": pdf_file_contents_hash,
            "pdf_file_as_txt_file_path": pdf_file_as_txt_file_path,
        }
        self._save_mapping_table()

    def get_pdf_contents_from_mapping_table(self, pdf_file_path: str):
        pdf_file_hash = get_file_hash(pdf_file_path)
        for pdf_file_path_key, pdf_file_mapping_data in self.mapping_table.items():
            mapping_pdf_file_hash = pdf_file_mapping_data.get("pdf_file_hash")
            if pdf_file_hash == mapping_pdf_file_hash:
                return read_txt_file(pdf_file_mapping_data.get("pdf_file_as_txt_file_path"))
        return None

    def parse_pdf_file(self, pdf_file_path: str) -> tuple[str, bool]:
        """
        Parse a PDF file and return its contents as text.
        """
        is_image_pdf = False
        # Check if the file is already in the mapping table
        # (to avoid re-processing the same file)
        pdf_contents_from_mapping_table = self.get_pdf_contents_from_mapping_table(pdf_file_path)
        if pdf_contents_from_mapping_table:
            is_image_pdf = True
            return pdf_contents_from_mapping_table, is_image_pdf

        # Parse the PDF file
        pdf_file_contents = parse_pdf_with_pymupdf(pdf_file_path)
        # if the text is empty, try to parse it as an image
        if not pdf_file_contents:
            print(
                f"[!] PDF file contents are empty. "
                f"Trying OCR to extract text: '{pdf_file_path}'"
            )
            # parse the pdf as an image
            pdf_file_contents = parse_pdf_with_pdf2image(pdf_file_path)
            # add the parsed text to the mapping table
            self.add_pdf_image_to_mapping_table(pdf_file_path, pdf_file_contents)
            is_image_pdf = True
        return pdf_file_contents, is_image_pdf


def get_pdf_file_contents(pdf_filepath: str):
    file_contents = None
    with open(pdf_filepath, 'r') as f_obj:
        file_contents = f_obj.read()
    return file_contents


def parse_pdf_with_pdfminer(pdf_path):
    text = extract_text(pdf_path)
    return text


def parse_pdf_with_pymupdf(pdf_path: str):
    doc = fitz.open(pdf_path)
    text = ""

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text += page.get_text()

    doc.close()
    return text


def parse_pdf_with_pdf2image(pdf_path: str):
    # Convert PDF to images
    print("Running OCR parsing process...")
    images = convert_from_path(pdf_path)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image)

    return text


def get_pdf_file_size(pdf_file_path) -> int:
    try:
        # Get the size of the file in bytes
        size_bytes = os.path.getsize(pdf_file_path)
        return size_bytes
    except FileNotFoundError:
        print(f"File not found: {pdf_file_path}")
