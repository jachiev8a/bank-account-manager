from banks.account_state_manager import PDFBankAccountStateManager
from pdf_utils.base import get_pdf_files
from pdf_utils.parsers import parse_pdf_with_pdfminer, parse_pdf_with_pymupdf


DIR_LIST_WITH_TO_LOOK_FOR_PDFS = [
    # "~/Downloads",
    "~/Downloads/PDF_TESTS",
]

ACCOUNT_STATE_OBJECTS = []

bank_account_state_manager = PDFBankAccountStateManager()
bank_account_state_manager.load_directories_to_search_for_pdfs(
    directory_list=DIR_LIST_WITH_TO_LOOK_FOR_PDFS
)

bank_account_state_manager.auto_rename_bank_accounts_loaded()
bank_account_state_manager.list_bank_accounts_loaded()

a = 0
