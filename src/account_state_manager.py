import os
import shutil
from datetime import datetime
import settings
from src.banks.banamex import BanamexDebitPDF, BanamexCreditCostco2025FormatPDF

from src.banks.base_classes import (
    BankAccountStatePDF,
    UnknownBankAccountStatePDF,
)
from src.banks.bbva import (
    BbvaDebitPDF,
    BbvaCreditPDF,
    BbvaCreditIpnPDF
)
from src.banks.citibanamex import (
    CitiBanamexDebitPDF
)
from src.banks.inbursa import InbursaDebitPDF
from src.banks.santander import (
    SantanderDebitPDF,
    SantanderDebitImagePDF
)
from pdf_utils.base import get_pdf_files
from pdf_utils.parsers import PdfParseManager


class PDFBankAccountStateManager:
    """
    Class to manage the bank accounts loaded from PDF files
    """

    _SEPARATOR = "="*80
    _SEPARATOR_SMALL = "-"*80

    OUTPUT_DIR = f"{settings.get_tmp_dir()}/_PDFBankAccountStateManager"

    def __init__(
        self,
        enable_auto_rename: bool = True
    ):
        """Constructor for the PDFBankAccountStateManager class.

        Args:
            enable_auto_rename (bool): If True, the bank account files
                will be renamed automatically to a human-readable format.
        """
        self.bank_accounts_loaded: dict[str, BankAccountStatePDF] = {}
        self.bank_accounts_to_ignore: list[BankAccountStatePDF] = []
        self.after_date_config: datetime.date = (
            settings.get_bank_account_after_date_config()
        )
        self.before_date_config: datetime.date = (
            settings.get_bank_account_before_date_config()
        )
        self.pdf_parser_manager = PdfParseManager()
        self.auto_rename_enabled = enable_auto_rename
        print(
            "[PDFBankAccountStateManager] initialized. "
            f"After Date Config: [{self.after_date_config}] | "
            f"Before Date Config: [{self.before_date_config}] | "
            f"Auto Rename Enabled: [{self.auto_rename_enabled}]"
        )

    def _load_bank_account_state_object(
        self,
        bank_account_state_object: BankAccountStatePDF
    ):
        """
        Load the BankAccountStatePDF object into the bank_accounts_loaded dictionary.
        """
        hash_file_value = bank_account_state_object.get_unique_hash_file_value()
        self.bank_accounts_loaded[hash_file_value] = bank_account_state_object

    def get_bank_account(self, bank_account: BankAccountStatePDF) -> BankAccountStatePDF:
        """Get a bank account by its unique hash file value.

        Args:
            bank_account (BankAccountStatePDF): The bank account object to get.

        Returns:
            BankAccountStatePDF: The bank account object if found, None otherwise.
        """
        hash_file_value = bank_account.get_unique_hash_file_value()
        return self.bank_accounts_loaded.get(hash_file_value, None)

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

    def is_bank_account_state_object_already_loaded(self, bank_account_state_object: BankAccountStatePDF):
        hash_file_value = bank_account_state_object.get_unique_hash_file_value()
        if hash_file_value in self.bank_accounts_loaded.keys():
            return True
        return False

    def load_directories_to_search_for_pdfs(
        self,
        directory_list: list = None
    ):
        """Load all PDF files found in the directories configured.
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
        if self.auto_rename_enabled:
            self.auto_rename_bank_accounts_loaded()
            print("Bank accounts files renamed successfully.")

    def load_bank_account_pdf_file(self, pdf_file_path: str):
        """Load a bank account PDF file and process it.

        This method builds a BankAccountStatePDF object from the PDF file,
        checks if it is already loaded, and verifies if it falls within the
        configured date range. If the file is valid and not already loaded,
        it will be added to the bank_accounts_loaded dictionary.

        If the file is out of the date range configured, it will be ignored.

        If auto-renaming is enabled, the file will be renamed to a human-readable
        format if it is not already renamed.

        Args:
            pdf_file_path (str): The path to the PDF file to be processed.

        Returns:
            None: If the PDF file is not a valid bank account state file
                or if it is out of the date range configured.
        """
        bank_account_state_obj = (
            self.build_bank_account_state_object_from_pdf_file(pdf_file_path)
        )
        if not bank_account_state_obj:
            return

        # Check if the bank account state object is already loaded
        if self.is_bank_account_state_object_already_loaded(bank_account_state_obj):
            bank_account_state_obj_already_loaded = (
                self.get_bank_account(bank_account_state_obj)
            )
            print(
                "[!] WARNING. PDF file already loaded! | "
                "Files seems to be the same: "
                f"[LOADED]: '{bank_account_state_obj_already_loaded.get_pdf_file_path()}' | "
                f"[IGNORED]: '{bank_account_state_obj.get_pdf_file_path()}' | "
            )
            bank_account_state_obj.set_as_ignored(
                "File already loaded | File: "
                f"'{bank_account_state_obj_already_loaded.get_pdf_file_path()}'"
            )

        # If the bank account state object is not already loaded,
        # perform further checks and load it if necessary.
        bank_account_period_date = bank_account_state_obj.get_periodo_inicio()
        bank_account_period_date = (
            datetime.strptime(bank_account_period_date, "%Y-%m-%d").date()
        )

        # Check if the bank account is in the specified date range
        is_bank_account_in_config_date_range = (
            self.after_date_config <= bank_account_period_date <= self.before_date_config
        )

        if not is_bank_account_in_config_date_range:
            print(
                f" > Bank Account PDF file '{pdf_file_path}' "
                "was ignored because it is out of the date range configured. "
                f"Period Date: '{bank_account_period_date}' "
                f"Date Range: [{self.after_date_config}] - [{self.before_date_config}]"
            )
            return

        # rename the file if auto-rename is enabled
        if self.auto_rename_enabled:
            bank_account_state_obj.auto_rename_file_name()

        if bank_account_state_obj.is_ignored:
            self.bank_accounts_to_ignore.append(bank_account_state_obj)
            return

        # all checks passed, load the bank account state object
        self._load_bank_account_state_object(bank_account_state_obj)

    def auto_rename_bank_accounts_loaded(self):
        for bank_account_obj_id, bank_account_obj in self.bank_accounts_loaded.items():
            bank_account_obj.auto_rename_file_name()

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
            print(
                f" > File: \"{bank_account_obj.get_pdf_file_path()}\" "
                f"is [IGNORED] | Reason: {bank_account_obj.ignored_reason}"
            )

    @staticmethod
    def is_bank_account_type_enabled(
        bank_account_obj: BankAccountStatePDF
    ) -> bool:
        is_bank_account_type_enabled = (
            (
                settings.is_debit_account_type_enabled()
                and bank_account_obj.is_debit_account()
            ) or (
                settings.is_credit_account_type_enabled()
                and bank_account_obj.is_credit_account()
            )
        )
        return is_bank_account_type_enabled

    def build_output_project(self, start_clean: bool = True):
        """
        Build the project with the bank accounts loaded.
        """
        if start_clean and os.path.exists(self.OUTPUT_DIR):
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
    def build_bank_account_state_object_from_pdf_file(cls, pdf_file_path: str):
        """Build <BankAccountStatePDF> object from the PDF file.

        Args:
            pdf_file_path (str): The path to the PDF file to be processed.

        Returns:
            BankAccountStatePDF: An instance of a subclass of BankAccountStatePDF
                if the PDF file matches any known format, otherwise None.
        """
        instance = None
        pdf_parse_manager = PdfParseManager()
        pdf_file_contents, is_pdf_image_type = (
            pdf_parse_manager.parse_pdf_file(pdf_file_path)
        )

        if BanamexCreditCostco2025FormatPDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = BanamexCreditCostco2025FormatPDF(pdf_file_path, pdf_file_contents)

        elif BanamexDebitPDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = BanamexDebitPDF(pdf_file_path, pdf_file_contents)

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

        elif BbvaCreditIpnPDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = BbvaCreditIpnPDF(pdf_file_path, pdf_file_contents)

        elif InbursaDebitPDF.keywords_found_in_pdf_contents(pdf_file_contents):
            instance = InbursaDebitPDF(pdf_file_path, pdf_file_contents)

        elif UnknownBankAccountStatePDF.keywords_found_in_pdf_contents(pdf_file_contents):
            a = 0

        if instance:
            print(f" > Bank State account successfully loaded: '{pdf_file_path}'")
            return instance
