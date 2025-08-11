import re
import os
from abc import ABC
from datetime import datetime
from typing import Union

import settings
from common.logging import CustomLogger
from common.utils import (
    convert_bytes_to_human_readable,
    get_hash_from_string
)
from pdf_utils.parsers import (
    parse_pdf_with_pymupdf,
    get_pdf_file_size
)


class BankAccountStatePDF(ABC):

    _SEPARATOR = "-"*70

    BANK_NAME = None
    BANK_SHORT_NAME = None
    PDF_KEYWORDS = []

    ALL_KEYWORDS_SHOULD_BE_IN_PDF = False

    PATTERN_FECHA_DE_CORTE = None
    PATTERN_PERIODO = None

    PATTERN_NUMERO_DE_CUENTA = None
    PATTERN_NUMERO_DE_CLIENTE = None
    PATTERN_NUMERO_DE_TARJETA = None

    # limit
    MAX_LIMIT_TO_SEARCH_FOR_KEYWORDS = None

    _SHORT_MONTH_MAPPING_ESP_TO_ENG = {
        'ene': 'enero',
        'feb': 'febrero',
        'mar': 'marzo',
        'abr': 'abril',
        'may': 'mayo',
        'jun': 'junio',
        'jul': 'julio',
        'ago': 'agosto',
        'sep': 'septiembre',
        'oct': 'octubre',
        'nov': 'noviembre',
        'dic': 'diciembre'
    }

    # Map Spanish month names to English month names
    _MONTH_MAPPING_ESP_TO_ENG = {
        'enero': 'January',
        'febrero': 'February',
        'marzo': 'March',
        'abril': 'April',
        'mayo': 'May',
        'junio': 'June',
        'julio': 'July',
        'agosto': 'August',
        'septiembre': 'September',
        'octubre': 'October',
        'noviembre': 'November',
        'diciembre': 'December'
    }

    _MONTH_MAPPING_SPANISH_BY_NUMBER = {
        1: 'Enero',
        2: 'Febrero',
        3: 'Marzo',
        4: 'Abril',
        5: 'Mayo',
        6: 'Junio',
        7: 'Julio',
        8: 'Agosto',
        9: 'Septiembre',
        10: 'Octubre',
        11: 'Noviembre',
        12: 'Diciembre',
    }

    # Regex Patterns for dates
    #   > '15 al 15 marzo de 2024'
    RE_PATTERN__DD_AL_DD_MONTH_DE_YYYY = r'^(\d{2})\s*al\s*(\d{2})\s*de\s*(\w+)+\s*de\s*(\d{4})$'
    #   > '15 de marzo de 2024'
    RE_PATTERN__DD_DE_MONTH_DE_YYYY = r'^(\d{1,2})\s*de\s*(\w+)+\s*de\s*(\d{4})$'
    #   > '15 de 03 de 24'
    RE_PATTERN__DD_DE_MM_DE_YY = r'^(\d{1,2})\s*de\s*(\d{1,2})\s*de\s*(\d{2})$'
    #   > '15 de marzo al 15 de abril de 2024'
    RE_PATTERN__DD_DE_MONTH_AL_DD_DE_MONTH_DE_YYYY = (
        r'^(\d{1,2})\s*de\s*(\w+)\s*al\s*(\d{1,2})\s*de\s*(\w+)+\s*de[l]?\s*(\d{4})$'
    )
    #   > '15 de marzo del 2024 al 15 de abril del 2024'
    RE_PATTERN__DD_DE_MONTH_DEL_YYYY_AL_DD_DE_MONTH_DEL_YYYY = (
        r'^(\d{1,2})\s*de\s*(\w+)+\s*de[l]?\s*(\d{4})\s*al\s*(\d{1,2})\s*de\s*(\w+)+\s*de[l]?\s*(\d{4})$'
    )
    #   > '15-Mar-2024 al 15-Ago-2024'
    RE_PATTERN__DD_dash_MONTH_dash_YYYY_AL_DD_dash_MONTH_dash_YYYY = (
        r'^(\d{1,2})\-(\w+)\-(\d{4})\s*al\s*(\d{1,2})\-(\w+)\-(\d{4})$'
    )
    #   > '15-Mar-2024'
    RE_PATTERN__DD_dash_MONTH_dash_YYYY = (
        r'^(\d{1,2})\-(\w+)\-(\d{4})$'
    )
    #   > '15 Ago 2024'
    #   > '15 Feb. 2024'
    RE_PATTERN__DD_MMM_YYYY = (
        r'^(\d{1,2})\s*(\w{3})\.?\s*(\d{4})$'
    )
    #   > '01 Ago 2024 al 31 Ago 2024'
    #   > '01 Feb. 2024 al 31 Feb. 2024'
    RE_PATTERN__DD_MMM_YYYY_AL_DD_MMM_YYYY = (
        r'^(\d{1,2})\s*(\w{3})\.?\s*(\d{4})\s*al\s*(\d{1,2})\s*(\w{3})\.?\s*(\d{4})$'
    )
    #   > '10/01/2024'
    RE_PATTERN__DD_slash_MM_slash_YYYY = (
        r'^\s?(\d{1,2})\/(\d{1,2})\/(\d{4})$'
    )
    #   > '10/01/24'
    RE_PATTERN__DD_slash_MM_slash_YY = (
        r'^\s?(\d{1,2})\/(\d{1,2})\/(\d{2})$'
    )
    #   > '11/12/2023 al 10/01/2024'
    RE_PATTERN__DD_slash_MM_slash_YYYY_AL_DD_slash_MM_slash_YYYY = (
        r'^\s?(\d{1,2})\/(\d{1,2})\/(\d{4})\s*al\s*(\d{1,2})\/(\d{1,2})\/(\d{4})$'
    )
    #   > '17/03/24 al 16/04/24'
    RE_PATTERN__DD_slash_MM_slash_YY_AL_DD_slash_MM_slash_YY = (
        r'^\s?(\d{1,2})\/(\d{1,2})\/(\d{2})\s*al\s*(\d{1,2})\/(\d{1,2})\/(\d{2})$'
    )

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None, is_image_pdf: bool = False):
        self.logger = CustomLogger(
            name=self.__class__.__name__,
            level=settings.get_log_level(),
        )
        self._bank_name = self.BANK_NAME
        self._bank_short_name = self.BANK_SHORT_NAME

        # build file paths and file metadata
        self.pdf_file_path = pdf_file_path
        self.pdf_file_basename = str(os.path.basename(pdf_file_path))
        self.pdf_file_dir_name = str(os.path.dirname(pdf_file_path))
        self.is_image_pdf = is_image_pdf

        # Load the raw file contents if not provided
        if raw_file_contents is None:
            self.raw_pdf_file_contents = self._load_raw_pdf_file_contents()
        self.raw_pdf_file_contents = raw_file_contents

        self.raw_data = {}

        self.fecha_de_corte: Union[datetime, None] = None
        self.periodo_inicio: Union[datetime, None] = None
        self.periodo_termino: Union[datetime, None] = None
        self.numero_de_cuenta: Union[str, None] = None
        self.numero_de_tarjeta: Union[str, None] = None
        self.numero_de_cliente: Union[str, None] = None

        self.is_debit = False
        self.is_credit = False
        self.month_name: Union[str, None] = None
        self.month_short_name: Union[str, None] = None

        self.file_size_in_bytes = get_pdf_file_size(pdf_file_path)
        self.file_size_human_readable = convert_bytes_to_human_readable(
            self.file_size_in_bytes
        )

        self.unique_hash_file_value = get_hash_from_string(
            self.raw_pdf_file_contents
        )

        self.is_duplicate = False
        self.is_ignored = False
        self.ignored_reason = ""

        # parse the pdf file and load the data into the instance
        self.load_bank_data_from_pdf()
        self._validate_fields()

    def _load_raw_pdf_file_contents(self):
        file_contents = parse_pdf_with_pymupdf(self.pdf_file_path)
        return file_contents

    def _validate_fields(self):
        main_empty_fields = []
        minor_empty_fields = []

        # main
        if not self.fecha_de_corte:
            main_empty_fields.append("fecha_de_corte")
        if not self.periodo_inicio:
            main_empty_fields.append("periodo_inicio")
        if not self.periodo_termino:
            main_empty_fields.append("periodo_termino")

        # minor
        if not self.numero_de_tarjeta and self.PATTERN_NUMERO_DE_TARJETA:
            minor_empty_fields.append("numero_de_tarjeta")
        if not self.numero_de_cuenta:
            minor_empty_fields.append("numero_de_cuenta")
        if not self.numero_de_cliente:
            minor_empty_fields.append("numero_de_cliente")

        # raise error if main fields are empty
        if main_empty_fields:
            error_msg = (
                f"[{self.__class__.__name__}] ERROR: some important fields "
                f"were empty after the parsing process... | "
                f"Bank: '{self.get_bank_name()}' | "
                f"PDF File: '{self.get_pdf_file_path()}' | "
                f"Fields: [{', '.join(main_empty_fields)}]"
            )
            raise RuntimeError(error_msg)
        elif minor_empty_fields:
            warning_msg = (
                "[!] WARNING: minor fields were empty after the parsing process... | "
                f"Bank: '{self.get_bank_name()}' | PDF File: '{self.get_pdf_file_path()}' | "
                f"Fields: [{', '.join(minor_empty_fields)}]"
            )
            print(warning_msg)

        # post-process
        self.month_name = self._MONTH_MAPPING_SPANISH_BY_NUMBER.get(
            self.periodo_inicio.month
        )
        self.month_short_name = self.month_name[:3].upper()

    def get_pdf_file_path(self):
        return self.pdf_file_path

    def get_fecha_de_corte(self, month_as_name: bool = False):
        if month_as_name:
            self.fecha_de_corte.strftime('%Y-%M-%d')
        return self.fecha_de_corte.strftime('%Y-%m-%d')

    def get_periodo_inicio(self) -> str:
        return self.periodo_inicio.strftime('%Y-%m-%d')

    def get_periodo_termino(self) -> str:
        return self.periodo_termino.strftime('%Y-%m-%d')

    def get_account_type_name(self) -> str:
        if self.is_credit_account():
            return "credito"
        elif self.is_debit_account():
            return "debito"

    def get_bank_name(self) -> str:
        return self._bank_name

    def get_bank_short_name(self) -> str:
        return self._bank_short_name

    def get_unique_hash_file_value(self) -> str:
        return self.unique_hash_file_value

    def get_human_readable_name(
        self,
        with_extension: bool = False
    ) -> str:
        """Generates a human-readable name for the PDF file.

        Args:
            with_extension: If True, the file name will
                include the '.pdf' extension.

        Returns:
            str: A human-readable name for the PDF file.
        """
        file_name = (
            f"{self.get_bank_short_name()}_"
            f"{self.get_account_type_name()}__"
            f"{self.get_periodo_inicio()}__"
            f"{self.month_short_name}"
        )
        if with_extension:
            file_name += ".pdf"
        return file_name

    def get_unique_name(self) -> str:
        return (
            f"{self.get_bank_name()}__"
            f"{self.numero_de_cuenta}__"
            f"{self.get_periodo_inicio()}__"
            f"{self.get_periodo_termino()}"
        )

    def get_unique_file_id(self) -> str:
        return (
            f"{self.get_bank_name()}__"
            f"{self.get_periodo_inicio()}__"
            f"{self.get_periodo_termino()}__"
            f"corte__{self.get_fecha_de_corte()}__"
            f"size__{self.file_size_in_bytes}"
        )

    def get_detail_report(self):
        return (
            f"{self._SEPARATOR}\n"
            f"[PDF]: '{self.pdf_file_basename}'\n"
            f" > [Banco]: '{self.get_bank_name()}'\n"
            f" > [Fecha-Corte]: '{self.get_fecha_de_corte()}'\n"
            f" > [Periodo-Reporte]: '{self.get_periodo_inicio()}' -> '{self.get_periodo_termino()}'\n"
            f" > [Fecha-Reporte]: '{self.month_name}'\n"
            f"{self._SEPARATOR}\n"
        )

    def is_debit_account(self) -> bool:
        return self.is_debit

    def is_credit_account(self) -> bool:
        return self.is_credit

    def is_file_already_renamed(self) -> bool:
        """Checks if the PDF file has already been renamed to a human-readable format.

        Returns:
            bool: True if the file is already renamed, False otherwise.
        """
        return (
            self.pdf_file_basename ==
            self.get_human_readable_name(with_extension=True)
        )

    def set_new_file_name(self, new_file_name: str):
        self.pdf_file_path = new_file_name
        self.pdf_file_basename = str(os.path.basename(new_file_name))
        self.pdf_file_dir_name = str(os.path.dirname(new_file_name))

    def set_as_ignored(self, reason: str = None):
        """Marks the PDF file as ignored, meaning it has already been processed or is not relevant.
        This method sets the `is_ignored` attribute to True and logs a message indicating that the file is ignored.
        """
        self.is_ignored = True
        if reason:
            self.ignored_reason = reason

        self.logger.info(
            f"[!] Ignored PDF Bank Account file: '{self.pdf_file_path}' | "
            f"Reason: {self.ignored_reason if self.ignored_reason else 'N/A'}"
        )

    def auto_rename_file_name(self):
        """Renames the PDF file to a human-readable name based on its contents.

        If the file already exists with the new name, it does not rename it.
        If the file cannot be renamed, it prints an error message.

        Returns:
            str: The new file name if the file was renamed,
                otherwise None.
        """
        # check if the file is already renamed to a human-readable format.
        if self.is_file_already_renamed():
            return None

        new_file_name_to_set = (
            f"{self.pdf_file_dir_name}/"
            f"{self.get_human_readable_name()}.pdf"
        )
        file_exists_with_new_name = os.path.exists(new_file_name_to_set)

        file_exists_with_new_name_but_is_not_this_file = (
            file_exists_with_new_name and
            self.pdf_file_path != new_file_name_to_set
        )

        if file_exists_with_new_name_but_is_not_this_file:
            # file already exists with the new name, but it is not this same file,
            # so we cannot rename it. And we should ignore this file.
            self.set_as_ignored(
                "File not able to be renamed because "
                "a file with the new name already exists. "
                f"New file: '{new_file_name_to_set}'"
            )
            return None

        if not file_exists_with_new_name:
            # file does not exist, so we can rename it
            print(
                f"[auto-rename] '{self.pdf_file_path}' "
                f"-> '{new_file_name_to_set}'"
            )
            os.rename(self.pdf_file_path, new_file_name_to_set)
            self.set_new_file_name(new_file_name_to_set)
            return new_file_name_to_set

    @classmethod
    def keywords_found_in_pdf_contents(cls, pdf_contents: str):
        pdf_contents_as_lines = pdf_contents.split("\n")
        if cls.MAX_LIMIT_TO_SEARCH_FOR_KEYWORDS is not None:
            pdf_contents_as_lines = pdf_contents_as_lines[:cls.MAX_LIMIT_TO_SEARCH_FOR_KEYWORDS]

        pdf_contents_as_text = "\n".join(pdf_contents_as_lines)

        total_keywords_found = 0

        for keyword in cls.PDF_KEYWORDS:
            if keyword in pdf_contents_as_text:
                if cls.ALL_KEYWORDS_SHOULD_BE_IN_PDF:
                    total_keywords_found += 1
                    if total_keywords_found == len(cls.PDF_KEYWORDS):
                        return True
                else:
                    return True
        return False

    @classmethod
    def format_date_period_string_into_datetime_tuple(cls, date_period_string):
        """
        Formats:
            '4 de febrero al 3 de marzo del 2024'
        """
        date_period_string = date_period_string.lower()
        date_data = cls.get_datetime_data_from_date_string(date_period_string)

        start_day = date_data.get("start_day")
        start_month = date_data.get("start_month")
        end_day = date_data.get("end_day")
        end_month = date_data.get("end_month")
        start_year = date_data.get("start_year")
        end_year = date_data.get("end_year")

        # Handle year offset in case of December being the start month
        # and January being the end month.
        # e.g. '4 de diciembre al 3 de enero del 2024'
        year_offset = 0
        if start_month.lower() == 'diciembre' and end_month.lower() == 'enero':
            year_offset = 1

        start_date_str = f"{start_day} de {start_month} de {int(start_year)-year_offset}"
        end_date_str = f"{end_day} de {end_month} de {end_year}"

        # Create datetime objects
        start_date = cls.format_date_string_into_datetime(start_date_str)
        end_date = cls.format_date_string_into_datetime(end_date_str)

        return start_date, end_date

    @classmethod
    def get_regex_pattern_from_date_string(cls, date_string):
        date_string = date_string.lower()
        pattern_name = None
        pattern = None
        if re.match(cls.RE_PATTERN__DD_AL_DD_MONTH_DE_YYYY, date_string):
            pattern_name = "DD_AL_DD_MONTH_DE_YYYY"
            pattern = cls.RE_PATTERN__DD_AL_DD_MONTH_DE_YYYY
        elif re.match(cls.RE_PATTERN__DD_DE_MONTH_DE_YYYY, date_string):
            pattern_name = "DD_DE_MONTH_DE_YYYY"
            pattern = cls.RE_PATTERN__DD_DE_MONTH_DE_YYYY
        elif re.match(cls.RE_PATTERN__DD_DE_MM_DE_YY, date_string):
            pattern_name = "DD_DE_MM_DE_YY"
            pattern = cls.RE_PATTERN__DD_DE_MM_DE_YY
        elif re.match(cls.RE_PATTERN__DD_DE_MONTH_AL_DD_DE_MONTH_DE_YYYY, date_string):
            pattern_name = "DD_DE_MONTH_AL_DD_DE_MONTH_DE_YYYY"
            pattern = cls.RE_PATTERN__DD_DE_MONTH_AL_DD_DE_MONTH_DE_YYYY
        elif re.match(cls.RE_PATTERN__DD_DE_MONTH_DEL_YYYY_AL_DD_DE_MONTH_DEL_YYYY, date_string):
            pattern_name = "DD_DE_MONTH_DEL_YYYY_AL_DD_DE_MONTH_DEL_YYYY"
            pattern = cls.RE_PATTERN__DD_DE_MONTH_DEL_YYYY_AL_DD_DE_MONTH_DEL_YYYY
        elif re.match(cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY_AL_DD_dash_MONTH_dash_YYYY, date_string):
            pattern_name = "DD_dash_MONTH_dash_YYYY_AL_DD_dash_MONTH_dash_YYYY"
            pattern = cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY_AL_DD_dash_MONTH_dash_YYYY
        elif re.match(cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY, date_string):
            pattern_name = "DD_dash_MONTH_dash_YYYY"
            pattern = cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY
        elif re.match(cls.RE_PATTERN__DD_MMM_YYYY, date_string):
            pattern_name = "DD_MMM_YYYY"
            pattern = cls.RE_PATTERN__DD_MMM_YYYY
        elif re.match(cls.RE_PATTERN__DD_MMM_YYYY_AL_DD_MMM_YYYY, date_string):
            pattern_name = "DD_MMM_YYYY_AL_DD_MMM_YYYY"
            pattern = cls.RE_PATTERN__DD_MMM_YYYY_AL_DD_MMM_YYYY
        elif re.match(cls.RE_PATTERN__DD_slash_MM_slash_YYYY, date_string):
            pattern_name = "DD_slash_MM_slash_YYYY"
            pattern = cls.RE_PATTERN__DD_slash_MM_slash_YYYY
        elif re.match(cls.RE_PATTERN__DD_slash_MM_slash_YY, date_string):
            pattern_name = "DD_slash_MM_slash_YY"
            pattern = cls.RE_PATTERN__DD_slash_MM_slash_YY
        elif re.match(cls.RE_PATTERN__DD_slash_MM_slash_YYYY_AL_DD_slash_MM_slash_YYYY, date_string):
            pattern_name = "DD_slash_MM_slash_YYYY_AL_DD_slash_MM_slash_YYYY"
            pattern = cls.RE_PATTERN__DD_slash_MM_slash_YYYY_AL_DD_slash_MM_slash_YYYY
        elif re.match(cls.RE_PATTERN__DD_slash_MM_slash_YY_AL_DD_slash_MM_slash_YY, date_string):
            pattern_name = "DD_slash_MM_slash_YY_AL_DD_slash_MM_slash_YY"
            pattern = cls.RE_PATTERN__DD_slash_MM_slash_YY_AL_DD_slash_MM_slash_YY
        if not pattern:
            raise RuntimeError(
                f"RE Pattern not supported for date string value: '{date_string}'"
            )
        return pattern_name, pattern

    @classmethod
    def get_datetime_data_from_date_string(cls, date_string) -> dict:

        start_day = None
        start_month = None
        end_day = None
        end_month = None
        start_year = None
        end_year = None

        regex_pattern_name, regex_pattern = (
            cls.get_regex_pattern_from_date_string(date_string)
        )
        match_pattern = re.match(regex_pattern, date_string.lower())

        if regex_pattern == cls.RE_PATTERN__DD_AL_DD_MONTH_DE_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(3)
            end_day = match_pattern.group(2)
            end_month = start_month
            start_year = match_pattern.group(4)
            end_year = start_year

        elif (
            regex_pattern == cls.RE_PATTERN__DD_DE_MONTH_DE_YYYY
            or regex_pattern == cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY
            or regex_pattern == cls.RE_PATTERN__DD_DE_MM_DE_YY
        ):
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            start_year = match_pattern.group(3)
            end_year = start_year

        elif regex_pattern == cls.RE_PATTERN__DD_DE_MONTH_AL_DD_DE_MONTH_DE_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            end_day = match_pattern.group(3)
            end_month = match_pattern.group(4)
            start_year = match_pattern.group(5)
            end_year = start_year

        elif (
            regex_pattern == cls.RE_PATTERN__DD_DE_MONTH_DEL_YYYY_AL_DD_DE_MONTH_DEL_YYYY
            or regex_pattern == cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY_AL_DD_dash_MONTH_dash_YYYY
        ):
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            start_year = match_pattern.group(3)
            end_day = match_pattern.group(4)
            end_month = match_pattern.group(5)
            end_year = match_pattern.group(6)

        elif regex_pattern == cls.RE_PATTERN__DD_MMM_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            start_year = match_pattern.group(3)
            end_year = start_year

        elif regex_pattern == cls.RE_PATTERN__DD_MMM_YYYY_AL_DD_MMM_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            start_year = match_pattern.group(3)
            end_day = match_pattern.group(4)
            end_month = match_pattern.group(5)
            end_year = match_pattern.group(6)

        elif (
            regex_pattern == cls.RE_PATTERN__DD_slash_MM_slash_YYYY or
            regex_pattern == cls.RE_PATTERN__DD_slash_MM_slash_YY
        ):
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            start_year = match_pattern.group(3)
            end_year = start_year

        elif regex_pattern == cls.RE_PATTERN__DD_slash_MM_slash_YYYY_AL_DD_slash_MM_slash_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            start_year = match_pattern.group(3)
            end_day = match_pattern.group(4)
            end_month = match_pattern.group(5)
            end_year = match_pattern.group(6)

        elif regex_pattern == cls.RE_PATTERN__DD_slash_MM_slash_YY_AL_DD_slash_MM_slash_YY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            start_year = match_pattern.group(3)
            end_day = match_pattern.group(4)
            end_month = match_pattern.group(5)
            end_year = match_pattern.group(6)

        if start_month in cls._SHORT_MONTH_MAPPING_ESP_TO_ENG:
            start_month = cls._SHORT_MONTH_MAPPING_ESP_TO_ENG[start_month]
        if end_month in cls._SHORT_MONTH_MAPPING_ESP_TO_ENG:
            end_month = cls._SHORT_MONTH_MAPPING_ESP_TO_ENG[end_month]

        return {
            "regex_pattern_name": regex_pattern_name,
            "regex_pattern": regex_pattern,
            "start_day": start_day,
            "start_month": start_month,
            "end_day": end_day,
            "end_month": end_month,
            "start_year": start_year,
            "end_year": end_year,
        }

    @classmethod
    def format_date_string_into_datetime(cls, date_string):

        date_data = cls.get_datetime_data_from_date_string(date_string)
        day = date_data.get("start_day")
        month = date_data.get("start_month")
        start_year = date_data.get("start_year")

        # Convert month number to month name in Spanish
        # (to later one, convert the month name to English)
        if month.isdigit():
            month = cls._MONTH_MAPPING_SPANISH_BY_NUMBER.get(int(month)).lower()

        # Convert month name to English
        month = cls._MONTH_MAPPING_ESP_TO_ENG[month]

        # if year is two digits, convert it to four digits format
        if len(start_year) == 2:
            start_year = (
                f"20{start_year}"
                if int(start_year) < 50
                else f"19{start_year}"
            )

        # Create datetime object
        date_string = f"{day} {month} {start_year}"
        datetime_object = datetime.strptime(date_string, "%d %B %Y")

        return datetime_object

    @classmethod
    def format_datetime_into_standard(cls, datetime_date: datetime):
        return datetime_date.strftime("%y-%m-%d")

    def load_bank_data_from_pdf(self):

        # Use re.search to find the pattern in the text
        match_fecha_corte = re.search(
            self.PATTERN_FECHA_DE_CORTE,
            self.raw_pdf_file_contents
        )

        match_periodo = re.search(
            self.PATTERN_PERIODO,
            self.raw_pdf_file_contents
        )

        match_numero_de_cuenta = re.search(
            self.PATTERN_NUMERO_DE_CUENTA,
            self.raw_pdf_file_contents
        )

        match_numero_cliente = re.search(
            self.PATTERN_NUMERO_DE_CLIENTE,
            self.raw_pdf_file_contents
        )

        if match_fecha_corte:
            fecha_de_corte = match_fecha_corte.group(1)
            self.raw_data["fecha_de_corte"] = fecha_de_corte
            self.fecha_de_corte = (
                self.format_date_string_into_datetime(fecha_de_corte)
            )

        if match_periodo:
            periodo = match_periodo.group(1)
            self.raw_data["periodo"] = periodo
            self.periodo_inicio, self.periodo_termino = (
                self.format_date_period_string_into_datetime_tuple(periodo)
            )

        if match_numero_de_cuenta:
            self.numero_de_cuenta = match_numero_de_cuenta.group(1)

        if match_numero_cliente:
            self.numero_de_cliente = match_numero_cliente.group(1)

        if self.PATTERN_NUMERO_DE_TARJETA is not None:
            match_numero_de_tarjeta = re.search(
                self.PATTERN_NUMERO_DE_TARJETA,
                self.raw_pdf_file_contents
            )

            if match_numero_de_tarjeta:
                self.numero_de_tarjeta = match_numero_de_tarjeta.group(1)

    def __repr__(self):
        """String representation of the object for debugging purposes.

        Example:
            <BbvaDebitPDF | PDF: 'bbva_debito__2024-07-17__JUL.pdf'>
        """
        return (
            f"<{self.__class__.__name__}"
            f" | PDF: '{self.get_pdf_file_path()}'>"
        )


class UnknownBankAccountStatePDF(BankAccountStatePDF):
    """This class is used to represent a bank account state PDF file.
    It is an abstract class that should be inherited by specific bank account state PDF classes.
    """

    BANK_NAME = "UnknownBank"
    BANK_SHORT_NAME = "UnknownBank"
    PDF_KEYWORDS = [
        "banco",
    ]
