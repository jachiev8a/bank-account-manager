import os
from banks.base_classes import BankAccountStatePDF
from banks.citibanamex import CitiBanamexDebitPDF, CitiBanamexCreditCostcoPDF
from banks.santander import SantanderDebitPDF, SantanderDebitImagePDF
from common.utils import get_project_tmp_dir, load_json_file, read_txt_file, write_json_file
from pdf_utils.base import get_pdf_files
from pdf_utils.parsers import parse_pdf_with_pymupdf, parse_pdf_with_pdf2image


class PDFBankAccountStateManager:

    _SEPARATOR = "="*80
    _SEPARATOR_SMALL = "-"*80

    PDF_IMAGE_MAPPING_FILE_NAME = f"{get_project_tmp_dir()}/__PDF_IMAGE_MAPPING_TABLE.json"
    PDF_IMAGE_MAPPING_TXT_FILES_DIR_PATH = f"{get_project_tmp_dir()}/PDF_TXT_FILES"
    PDF_IMAGE_MAPPING_DATA = None

    def __init__(self):
        self.bank_accounts_loaded = {}  # type: dict[str, BankAccountStatePDF]

    def _load_bank_account_state_object(self, bank_account_state_object: BankAccountStatePDF):
        unique_file_id = bank_account_state_object.get_unique_file_id()
        self.bank_accounts_loaded[unique_file_id] = bank_account_state_object

    @classmethod
    def load_pdf_image_mapping_table(cls):
        if not os.path.exists(cls.PDF_IMAGE_MAPPING_FILE_NAME):
            with open(cls.PDF_IMAGE_MAPPING_FILE_NAME, "w") as f_obj:
                f_obj.write("{}")
        # print(f"Loading PDF Image Mapping Table ({pdf_image_mapping_file})...")
        cls.PDF_IMAGE_MAPPING_DATA = load_json_file(cls.PDF_IMAGE_MAPPING_FILE_NAME)
        os.makedirs(cls.PDF_IMAGE_MAPPING_TXT_FILES_DIR_PATH, exist_ok=True)

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
            new_file_name = bank_account_obj.auto_rename_file_name()
            if bank_account_obj.is_image_pdf and new_file_name:
                self.set_pdf_file_contents_to_mapping_table(
                    new_file_name,
                    bank_account_obj.raw_pdf_file_contents,
                )

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

    @classmethod
    def set_pdf_file_contents_to_mapping_table(cls, original_pdf_image_file_path: str, file_contents: str):
        cls.load_pdf_image_mapping_table()
        original_pdf_image_basename = original_pdf_image_file_path.split("/")[-1].split(".")[0]
        pdf_file_mapped_as_txt = (
            f"{cls.PDF_IMAGE_MAPPING_TXT_FILES_DIR_PATH}/{original_pdf_image_basename}.txt"
        )
        with open(pdf_file_mapped_as_txt, "w") as f_obj:
            f_obj.write(file_contents)
        cls.PDF_IMAGE_MAPPING_DATA[original_pdf_image_file_path] = pdf_file_mapped_as_txt
        write_json_file(
            cls.PDF_IMAGE_MAPPING_FILE_NAME,
            cls.PDF_IMAGE_MAPPING_DATA
        )

    @classmethod
    def get_pdf_file_contents_from_mapping_table(cls, pdf_file_path: str):
        cls.load_pdf_image_mapping_table()
        if pdf_file_path in cls.PDF_IMAGE_MAPPING_DATA.keys():
            print(f" > PDF file contents loaded from mapping table: '{pdf_file_path}'")
            pdf_file_mapped_as_txt = cls.PDF_IMAGE_MAPPING_DATA[pdf_file_path]
            file_contents = read_txt_file(pdf_file_mapped_as_txt)
            return file_contents

    @classmethod
    def get_bank_account_state_object_from_pdf_file(cls, pdf_file_path: str):
        instance = None
        is_image_pdf = False
        file_contents = cls.get_pdf_file_contents_from_mapping_table(pdf_file_path)
        if not file_contents:
            file_contents = parse_pdf_with_pymupdf(pdf_file_path)
            if not file_contents:
                print(
                    f"[!] PDF file contents are empty. "
                    f"Trying OCR to extract text: '{pdf_file_path}'"
                )
                file_contents = parse_pdf_with_pdf2image(pdf_file_path)
                is_image_pdf = True
                cls.set_pdf_file_contents_to_mapping_table(pdf_file_path, file_contents)
        else:
            is_image_pdf = True

        if CitiBanamexCreditCostcoPDF.keywords_found_in_pdf_contents(file_contents):
            instance = CitiBanamexCreditCostcoPDF(pdf_file_path, file_contents)

        elif CitiBanamexDebitPDF.keywords_found_in_pdf_contents(file_contents):
            instance = CitiBanamexDebitPDF(pdf_file_path, file_contents)

        elif is_image_pdf and SantanderDebitImagePDF.keywords_found_in_pdf_contents(file_contents):
            instance = SantanderDebitImagePDF(pdf_file_path, file_contents)

        elif SantanderDebitPDF.keywords_found_in_pdf_contents(file_contents):
            instance = SantanderDebitPDF(pdf_file_path, file_contents)

        if instance:
            print(f" > Bank State account successfully loaded: '{pdf_file_path}'")
            return instance
