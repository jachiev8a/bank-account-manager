from banks.base_classes import BankAccountStatePDF
from banks.citibanamex import CitiBanamexDebitPDF, CitiBanamexCreditCostcoPDF
from banks.santander import SantanderDebitPDF
from pdf_utils.base import get_pdf_files
from pdf_utils.parsers import parse_pdf_with_pymupdf


class PDFBankAccountStateManager:

    SEPARATOR = "="*80

    def __init__(self):
        self.bank_accounts_loaded = {}  # type: dict[str, BankAccountStatePDF]

    def _load_bank_account_state_object(self, bank_account_state_object: BankAccountStatePDF):
        unique_file_id = bank_account_state_object.get_unique_file_id()
        self.bank_accounts_loaded[unique_file_id] = bank_account_state_object

    def bank_account_state_object_already_loaded(self, bank_account_state_object: BankAccountStatePDF):
        unique_file_id = bank_account_state_object.get_unique_file_id()
        if unique_file_id in self.bank_accounts_loaded.keys():
            return True
        return False

    def load_directories_to_search_for_pdfs(self, directory_list: list = None):
        if not directory_list:
            directory_list = []

        pdf_files_abspath_list = []

        for directory in directory_list:
            files_found_in_dir = get_pdf_files(directory)
            pdf_files_abspath_list.extend(files_found_in_dir)

        for pdf_file_abspath in pdf_files_abspath_list:
            print(f"Processing PDF file: '{pdf_file_abspath}'")
            self.load_bank_account_pdf_file(pdf_file_abspath)

        print(
            "Finish Loading process. Total PDF bank accounts: "
            f"[{len(self.bank_accounts_loaded)}]"
        )

    def load_bank_account_pdf_file(self, pdf_file_path: str):
        bank_account_state_obj = (
            self.get_bank_account_state_object_from_pdf_file(pdf_file_path)
        )
        if bank_account_state_obj:
            if self.bank_account_state_object_already_loaded(bank_account_state_obj):
                print(
                    "[!] WARNING. PDF file already loaded! | "
                    "Files seems to be the same: "
                    f"[1]: '{pdf_file_path}' | "
                    f"[2]: '{bank_account_state_obj.get_pdf_file_path()}' | "
                )
            else:
                self._load_bank_account_state_object(bank_account_state_obj)

    def auto_rename_bank_accounts_loaded(self):
        for bank_account_obj_id, bank_account_obj in self.bank_accounts_loaded.items():
            bank_account_obj.auto_rename_file_name()

    def list_bank_accounts_loaded(self):
        print(self.SEPARATOR)
        for bank_account_obj_id, bank_account_obj in self.bank_accounts_loaded.items():
            print(
                f"> Account Loaded: [{bank_account_obj.get_bank_name()}]: "
                f"'{bank_account_obj.pdf_file_basename}'"
            )
        print(self.SEPARATOR)

    @classmethod
    def get_bank_account_state_object_from_pdf_file(cls, pdf_file_path: str):
        file_contents = parse_pdf_with_pymupdf(pdf_file_path)
        instance = None

        if CitiBanamexCreditCostcoPDF.keywords_found_in_pdf_contents(file_contents):
            instance = CitiBanamexCreditCostcoPDF(pdf_file_path)

        elif CitiBanamexDebitPDF.keywords_found_in_pdf_contents(file_contents):
            instance = CitiBanamexDebitPDF(pdf_file_path)

        elif SantanderDebitPDF.keywords_found_in_pdf_contents(file_contents):
            instance = SantanderDebitPDF(pdf_file_path)

        if instance:
            print(f" > Bank State account successfully loaded: '{pdf_file_path}'")
            return instance
