import os
import shutil
from datetime import datetime

from banks.base_classes import BankAccountStatePDF
from banks.bbva import BbvaDebitPDF, BbvaCreditPDF
from banks.citibanamex import CitiBanamexDebitPDF, CitiBanamexCreditCostcoPDF
from banks.inbursa import InbursaDebitPDF
from banks.santander import SantanderDebitPDF, SantanderDebitImagePDF
from pdf_utils.base import get_pdf_files
from pdf_utils.parsers import PdfParseManager
from settings import get_tmp_dir, get_bank_account_after_date_config, is_debit_account_type_enabled, \
    is_credit_account_type_enabled


class PDFBankAccountStateManager:
    """
    Class to manage the bank accounts loaded from PDF files
    """

    _SEPARATOR = "="*80
    _SEPARATOR_SMALL = "-"*80

    OUTPUT_DIR = f"{get_tmp_dir()}/_PDFBankAccountStateManager"

    def __init__(self):
        """
        Constructor for the PDFBankAccountStateManager class.
        """
        self.bank_accounts_loaded = {}  # type: dict[str, BankAccountStatePDF]
        self.bank_accounts_to_ignore = []  # type: list[BankAccountStatePDF]
        self.after_date_config = get_bank_account_after_date_config()  # type: datetime.date
        self.pdf_parser_manager = PdfParseManager()

    def _load_bank_account_state_object(
        self,
        bank_account_state_object: BankAccountStatePDF
    ):
        """
        Load the BankAccountStatePDF object into the bank_accounts_loaded dictionary.
        """
        hash_file_value = bank_account_state_object.get_unique_hash_file_value()
        self.bank_accounts_loaded[hash_file_value] = bank_account_state_object

    def get_bank_accounts_loaded_ordered(
        self,
        by_bank_name: bool = False,
        by_date: bool = False,
    ):
        if by_bank_name:
            return sorted(
                self.bank_accounts_loaded.values(),
                key=lambda x: x.get_bank_name()
            )
        elif by_date:
            return sorted(
                self.bank_accounts_loaded.values(),
                key=lambda x: x.get_periodo_inicio()
            )
        else:
            return self.bank_accounts_loaded.values()

    def get_bank_accounts_loaded_by_bank_name(self) -> dict[str, list[BankAccountStatePDF]]:
        """
        Get the bank accounts loaded by bank name.
        """
        bank_accounts_by_bank = {}
        for bank_account_obj_id, bank_account_obj in self.bank_accounts_loaded.items():
            bank_name = bank_account_obj.get_bank_name()
            if bank_name not in bank_accounts_by_bank.keys():
                bank_accounts_by_bank[bank_name] = []
            bank_accounts_by_bank[bank_name].append(bank_account_obj)
        return bank_accounts_by_bank

    def bank_account_state_object_already_loaded(self, bank_account_state_object: BankAccountStatePDF):
        hash_file_value = bank_account_state_object.get_unique_hash_file_value()
        if hash_file_value in self.bank_accounts_loaded.keys():
            return True
        return False

    def load_directories_to_search_for_pdfs(
        self,
        directory_list: list = None
    ):
        """
        Load the PDF files found in the directories specified in the 'directory_list' parameter.
        """
        if not directory_list:
            directory_list = []

        pdf_files_abspath_list = []

        for directory in directory_list:
            pdf_files_found_in_dir = get_pdf_files(directory)
            pdf_files_abspath_list.extend(pdf_files_found_in_dir)

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
                bank_account_state_obj_already_loaded = self.bank_accounts_loaded.get(
                    bank_account_state_obj.get_unique_hash_file_value()
                )
                print(
                    "[!] WARNING. PDF file already loaded! | "
                    "Files seems to be the same: "
                    f"[LOADED]: '{bank_account_state_obj_already_loaded.get_pdf_file_path()}' | "
                    f"[IGNORED]: '{bank_account_state_obj.get_pdf_file_path()}' | "
                )
                self.bank_accounts_to_ignore.append(bank_account_state_obj)
            else:
                bank_account_period_date = bank_account_state_obj.get_periodo_inicio()
                bank_account_period_date = datetime.strptime(bank_account_period_date, "%Y-%m-%d").date()
                if bank_account_period_date >= self.after_date_config:
                    self._load_bank_account_state_object(bank_account_state_obj)
                else:
                    print(
                        f" > Bank Account PDF file is older than the specified date: '{pdf_file_path}'"
                    )

    def auto_rename_bank_accounts_loaded(self):
        for bank_account_obj_id, bank_account_obj in self.bank_accounts_loaded.items():
            new_file_name = bank_account_obj.auto_rename_file_name()

    def list_bank_accounts_loaded(self, add_details: bool = False, order_by: str = None):
        print(self._SEPARATOR)
        print("Bank Accounts Loaded:")
        print(self._SEPARATOR)

        bank_accounts_loaded = self.get_bank_accounts_loaded_ordered(
            by_bank_name=False,
            by_date=False,
        )

        if order_by == "date":
            bank_accounts_loaded = self.get_bank_accounts_loaded_ordered(
                by_bank_name=False,
                by_date=True,
            )
        elif order_by == "bank":
            bank_accounts_loaded = self.get_bank_accounts_loaded_ordered(
                by_bank_name=True,
                by_date=False,
            )

        for bank_account_obj in bank_accounts_loaded:
            print(f" - {bank_account_obj.get_pdf_file_path()}")

            if add_details:
                print(f"    - Bank: '{bank_account_obj.get_bank_name()}'")
                print(f"    - Periodo: [{bank_account_obj.get_periodo_inicio()}] - [{bank_account_obj.get_periodo_termino()}]")
                print(f"    - Fecha de Corte: [{bank_account_obj.get_fecha_de_corte()}]")
                print(self._SEPARATOR_SMALL)

        print(self._SEPARATOR)

        for bank_account_obj in self.bank_accounts_to_ignore:
            print(f" > File: \"{bank_account_obj.get_pdf_file_path()}\" was ignored.")

    @staticmethod
    def is_bank_account_type_enabled(bank_account_obj: BankAccountStatePDF):
        if bank_account_obj.is_debit_account() and is_debit_account_type_enabled():
            return True
        elif bank_account_obj.is_credit_account() and is_credit_account_type_enabled():
            return True
        return False

    def build_output_project(self, start_clean: bool = True):
        """
        Build the project with the bank accounts loaded.
        """
        if start_clean:
            if os.path.exists(self.OUTPUT_DIR):
                shutil.rmtree(self.OUTPUT_DIR)

        bank_accounts_by_bank = self.get_bank_accounts_loaded_by_bank_name()
        for bank_name, bank_accounts_list in bank_accounts_by_bank.items():

            output_bank_dir = f"{self.OUTPUT_DIR}/{bank_name}"
            os.makedirs(output_bank_dir, exist_ok=True)

            for bank_account_obj in bank_accounts_list:
                if self.is_bank_account_type_enabled(bank_account_obj):
                    bank_account_type = bank_account_obj.get_account_type_name()
                    if not os.path.exists(f"{output_bank_dir}/{bank_account_type}"):
                        os.makedirs(f"{output_bank_dir}/{bank_account_type}")
                    output_file_path = (
                        f"{output_bank_dir}/"
                        f"{bank_account_type}/"
                        f"{bank_account_obj.pdf_file_basename}"
                    )
                    if not os.path.exists(output_file_path):
                        shutil.copyfile(
                            bank_account_obj.get_pdf_file_path(),
                            output_file_path
                        )


    @classmethod
    def get_bank_account_state_object_from_pdf_file(cls, pdf_file_path: str):
        """
        Get the BankAccountStatePDF object from the PDF file.
        """
        instance = None
        pdf_parse_manager = PdfParseManager()
        pdf_file_contents, is_pdf_image_type = (
            pdf_parse_manager.parse_pdf_file(pdf_file_path)
        )

        if CitiBanamexCreditCostcoPDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = CitiBanamexCreditCostcoPDF(pdf_file_path, pdf_file_contents)

        elif CitiBanamexDebitPDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = CitiBanamexDebitPDF(pdf_file_path, pdf_file_contents)

        elif is_pdf_image_type and SantanderDebitImagePDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = SantanderDebitImagePDF(pdf_file_path, pdf_file_contents)

        elif SantanderDebitPDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = SantanderDebitPDF(pdf_file_path, pdf_file_contents)

        elif BbvaDebitPDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = BbvaDebitPDF(pdf_file_path, pdf_file_contents)

        elif BbvaCreditPDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = BbvaCreditPDF(pdf_file_path, pdf_file_contents)

        elif InbursaDebitPDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = InbursaDebitPDF(pdf_file_path, pdf_file_contents)

        if instance:
            print(f" > Bank State account successfully loaded: '{pdf_file_path}'")
            return instance
