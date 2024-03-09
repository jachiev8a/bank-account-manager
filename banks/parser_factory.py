from banks.citibanamex import CitiBanamexPDF
from pdf_utils.parsers import parse_pdf_with_pymupdf


class PDFBankFactory:

    @classmethod
    def get_pdf_bank(cls, pdf_file_path: str):
        file_contents = parse_pdf_with_pymupdf(pdf_file_path)

        if CitiBanamexPDF.keywords_found_in_pdf_contents(file_contents):
            return CitiBanamexPDF(pdf_file_path)

