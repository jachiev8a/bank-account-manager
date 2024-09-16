import re
import os
from abc import ABC
from datetime import datetime
from typing import Union

import settings
from common.logging import CustomLogger
from common.utils import convert_bytes_to_human_readable, get_file_hash, get_hash_from_string
from pdf_utils.parsers import parse_pdf_with_pymupdf, get_pdf_file_size


class BankAccountStatePDF(ABC):

    _SEPARATOR = f"-"*70

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
    RE_PATTERN__DD_MMM_YYYY = (
        r'^(\d{1,2})\s*(\w{3})\s*(\d{4})$'
    )
    #   > '01 Ago 2024 al 31 Ago 2024'
    RE_PATTERN__DD_MMM_YYYY_AL_DD_MMM_YYYY = (
        r'^(\d{1,2})\s*(\w{3})\s*(\d{4})\s*al\s*(\d{1,2})\s*(\w{3})\s*(\d{4})$'
    )
    #   > '10/01/2024'
    RE_PATTERN__DD_slash_MM_slash_YYYY = (
        r'^\s?(\d{1,2})\/(\d{1,2})\/(\d{4})$'
    )
    #   > '11/12/2023 al 10/01/2024'
    RE_PATTERN__DD_slash_MM_slash_YYYY_AL_DD_slash_MM_slash_YYYY = (
        r'^\s?(\d{1,2})\/(\d{1,2})\/(\d{4})\s*al\s*(\d{1,2})\/(\d{1,2})\/(\d{4})$'
    )

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None, is_image_pdf: bool = False):
        self.logger = CustomLogger(
            name=self.__class__.__name__,
            level=settings.get_log_level(),
        )
        self._bank_name = self.BANK_NAME
        self._bank_short_name = self.BANK_SHORT_NAME
        self.pdf_file_path = pdf_file_path
        self.pdf_file_basename = str(os.path.basename(pdf_file_path))
        self.pdf_file_dir_name = str(os.path.dirname(pdf_file_path))
        self.is_image_pdf = is_image_pdf

        # Load the raw file contents if not provided
        if raw_file_contents is None:
            self.raw_pdf_file_contents = self._load_raw_pdf_file_contents()
        self.raw_pdf_file_contents = raw_file_contents

        self.raw_data = {}

        self.fecha_de_corte = None  # type: Union[datetime, None]
        self.periodo_inicio = None  # type: Union[datetime, None]
        self.periodo_termino = None  # type: Union[datetime, None]
        self.numero_de_cuenta = None  # type: Union[str, None]
        self.numero_de_tarjeta = None  # type: Union[str, None]
        self.numero_de_cliente = None  # type: Union[str, None]

        self.is_debit = False
        self.is_credit = False
        self.month_name = None  # type: Union[str, None]
        self.month_short_name = None  # type: Union[str, None]

        self.file_size_in_bytes = get_pdf_file_size(pdf_file_path)
        self.file_size_human_readable = convert_bytes_to_human_readable(
            self.file_size_in_bytes
        )

        self.unique_hash_file_value = get_hash_from_string(
            self.raw_pdf_file_contents
        )

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
                "ERROR: some important fields were empty after the parsing process... | "
                f"Bank: '{self.get_bank_name()}' | PDF File: '{self.get_pdf_file_path()}' | "
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

    def get_periodo_inicio(self):
        return self.periodo_inicio.strftime('%Y-%m-%d')

    def get_periodo_termino(self):
        return self.periodo_termino.strftime('%Y-%m-%d')

    def is_debit_account(self):
        return self.is_debit

    def is_credit_account(self):
        return self.is_credit

    def get_account_type_name(self):
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

    def get_human_readable_name(self) -> str:
        return (
            f"{self.get_bank_short_name()}_"
            f"{self.get_account_type_name()}__"
            f"{self.get_periodo_inicio()}__"
            f"{self.month_short_name}"
        )

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

    def auto_rename_file_name(self):
        new_file_name = f"{self.pdf_file_dir_name}/{self.get_human_readable_name()}.pdf"
        if not os.path.exists(new_file_name):
            if self.pdf_file_basename != new_file_name:
                print(f"[auto-rename] '{self.pdf_file_path}' -> '{new_file_name}'")
                os.rename(self.pdf_file_path, new_file_name)
                self.pdf_file_path = new_file_name
                return new_file_name
        elif self.pdf_file_path != new_file_name:
            print(
                f"[!] Not possible to rename the file '{self.pdf_file_path}' -> '{new_file_name}'"
            )

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

        start_day = date_data.get('start_day')
        start_month = date_data.get('start_month')
        end_day = date_data.get('end_day')
        end_month = date_data.get('end_month')
        year = date_data.get('year')

        # Handle year offset in case of December being the start month
        # and January being the end month.
        # e.g. '4 de diciembre al 3 de enero del 2024'
        year_offset = 0
        if start_month.lower() == 'diciembre' and end_month.lower() == 'enero':
            year_offset = 1

        start_date_str = f"{start_day} de {start_month} de {int(year)-year_offset}"
        end_date_str = f"{end_day} de {end_month} de {year}"

        # Create datetime objects
        start_date = cls.format_date_string_into_datetime(start_date_str)
        end_date = cls.format_date_string_into_datetime(end_date_str)

        return start_date, end_date

    @classmethod
    def get_regex_pattern_from_date_string(cls, date_string):
        date_string = date_string.lower()
        pattern = None
        if re.match(cls.RE_PATTERN__DD_AL_DD_MONTH_DE_YYYY, date_string):
            pattern = cls.RE_PATTERN__DD_AL_DD_MONTH_DE_YYYY
        elif re.match(cls.RE_PATTERN__DD_DE_MONTH_DE_YYYY, date_string):
            pattern = cls.RE_PATTERN__DD_DE_MONTH_DE_YYYY
        elif re.match(cls.RE_PATTERN__DD_DE_MONTH_AL_DD_DE_MONTH_DE_YYYY, date_string):
            pattern = cls.RE_PATTERN__DD_DE_MONTH_AL_DD_DE_MONTH_DE_YYYY
        elif re.match(cls.RE_PATTERN__DD_DE_MONTH_DEL_YYYY_AL_DD_DE_MONTH_DEL_YYYY, date_string):
            pattern = cls.RE_PATTERN__DD_DE_MONTH_DEL_YYYY_AL_DD_DE_MONTH_DEL_YYYY
        elif re.match(cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY_AL_DD_dash_MONTH_dash_YYYY, date_string):
            pattern = cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY_AL_DD_dash_MONTH_dash_YYYY
        elif re.match(cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY, date_string):
            pattern = cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY
        elif re.match(cls.RE_PATTERN__DD_MMM_YYYY, date_string):
            pattern = cls.RE_PATTERN__DD_MMM_YYYY
        elif re.match(cls.RE_PATTERN__DD_MMM_YYYY_AL_DD_MMM_YYYY, date_string):
            pattern = cls.RE_PATTERN__DD_MMM_YYYY_AL_DD_MMM_YYYY
        elif re.match(cls.RE_PATTERN__DD_slash_MM_slash_YYYY, date_string):
            pattern = cls.RE_PATTERN__DD_slash_MM_slash_YYYY
        elif re.match(cls.RE_PATTERN__DD_slash_MM_slash_YYYY_AL_DD_slash_MM_slash_YYYY, date_string):
            pattern = cls.RE_PATTERN__DD_slash_MM_slash_YYYY_AL_DD_slash_MM_slash_YYYY
        if not pattern:
            raise RuntimeError(
                f"RE Pattern not supported for date string value: '{date_string}'"
            )
        return pattern

    @classmethod
    def get_datetime_data_from_date_string(cls, date_string) -> dict:

        start_day = None
        start_month = None
        end_day = None
        end_month = None
        year = None

        regex_pattern = cls.get_regex_pattern_from_date_string(date_string)
        match_pattern = re.match(regex_pattern, date_string.lower())

        if regex_pattern == cls.RE_PATTERN__DD_AL_DD_MONTH_DE_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(3)
            end_day = match_pattern.group(2)
            end_month = start_month
            year = match_pattern.group(4)

        elif (
            regex_pattern == cls.RE_PATTERN__DD_DE_MONTH_DE_YYYY
            or regex_pattern == cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY
        ):
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            year = match_pattern.group(3)

        elif regex_pattern == cls.RE_PATTERN__DD_DE_MONTH_AL_DD_DE_MONTH_DE_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            end_day = match_pattern.group(3)
            end_month = match_pattern.group(4)
            year = match_pattern.group(5)

        elif (
            regex_pattern == cls.RE_PATTERN__DD_DE_MONTH_DEL_YYYY_AL_DD_DE_MONTH_DEL_YYYY
            or regex_pattern == cls.RE_PATTERN__DD_dash_MONTH_dash_YYYY_AL_DD_dash_MONTH_dash_YYYY
        ):
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            end_day = match_pattern.group(4)
            end_month = match_pattern.group(5)
            year = match_pattern.group(6)

        elif regex_pattern == cls.RE_PATTERN__DD_MMM_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            year = match_pattern.group(3)

        elif regex_pattern == cls.RE_PATTERN__DD_MMM_YYYY_AL_DD_MMM_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            end_day = match_pattern.group(4)
            end_month = match_pattern.group(5)
            year = match_pattern.group(6)

        elif regex_pattern == cls.RE_PATTERN__DD_slash_MM_slash_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            year = match_pattern.group(3)

        elif regex_pattern == cls.RE_PATTERN__DD_slash_MM_slash_YYYY_AL_DD_slash_MM_slash_YYYY:
            start_day = match_pattern.group(1)
            start_month = match_pattern.group(2)
            end_day = match_pattern.group(4)
            end_month = match_pattern.group(5)
            year = match_pattern.group(6)

        if start_month in cls._SHORT_MONTH_MAPPING_ESP_TO_ENG:
            start_month = cls._SHORT_MONTH_MAPPING_ESP_TO_ENG[start_month]
        if end_month in cls._SHORT_MONTH_MAPPING_ESP_TO_ENG:
            end_month = cls._SHORT_MONTH_MAPPING_ESP_TO_ENG[end_month]

        return {
            "start_day": start_day,
            "start_month": start_month,
            "end_day": end_day,
            "end_month": end_month,
            "year": year,
        }

    @classmethod
    def format_date_string_into_datetime(cls, date_string):

        date_data = cls.get_datetime_data_from_date_string(date_string)
        day = date_data.get("start_day")
        month = date_data.get("start_month")
        year = date_data.get("year")

        # Convert month number to month name in Spanish
        # (to later one, convert the month name to English)
        if month.isdigit():
            month = cls._MONTH_MAPPING_SPANISH_BY_NUMBER.get(int(month)).lower()

        # Convert month name to English
        month = cls._MONTH_MAPPING_ESP_TO_ENG[month]

        # Create datetime object
        date_string = f"{day} {month} {year}"
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
            self.fecha_de_corte = self.format_date_string_into_datetime(fecha_de_corte)

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
        return (
            f"<{self.__class__.__name__}"
            f" | PDF: '{self.get_pdf_file_path()}'>"
        )
