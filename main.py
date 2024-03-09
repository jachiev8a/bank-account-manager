from banks.parser_factory import PDFBankFactory
from pdf_utils.base import get_pdf_files
from pdf_utils.parsers import parse_pdf_with_pdfminer, parse_pdf_with_pymupdf

# Example usage:
DIR_TO_LOOK_FOR_PDFS = "~/Downloads"
pdf_files_list = get_pdf_files(DIR_TO_LOOK_FOR_PDFS)

for pdf_file in pdf_files_list:
    print(f"Processing PDF: '{pdf_file}'")
    pdf_bank_obj = PDFBankFactory.get_pdf_bank(pdf_file)
    a = 0
