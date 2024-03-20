import re
import os
from abc import ABC
from datetime import datetime
from typing import Union

from pdf_utils.parsers import parse_pdf_with_pymupdf, get_pdf_file_size


class BankAccountStatePDF(ABC):

    BANK_NAME = None
    BANK_SHORT_NAME = None
    PDF_KEYWORDS = []

    PATTERN_FECHA_DE_CORTE = None
    PATTERN_PERIODO = None

    PATTERN_NUMERO_DE_CUENTA = None
    PATTERN_NUMERO_DE_CLIENTE = None
    PATTERN_NUMERO_DE_TARJETA = None

    # Map Spanish month names to English month names
    _MONTH_MAPPING = {
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

    def __init__(self, pdf_file_path):
        self._bank_name = self.BANK_NAME
        self._bank_short_name = self.BANK_SHORT_NAME
        self.pdf_file_path = pdf_file_path
        self.pdf_file_basename = os.path.basename(pdf_file_path)
        self.pdf_file_dir_name = os.path.dirname(pdf_file_path)
        self.raw_pdf_file_contents = self._load_raw_pdf_file_contents()

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

        self.file_size = get_pdf_file_size(pdf_file_path)

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

        # post-process
        self.month_name = self._MONTH_MAPPING_SPANISH_BY_NUMBER.get(
            self.periodo_inicio.month
        )
        self.month_short_name = self.month_name[:3].upper()

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

    def get_pdf_file_path(self):
        return self.pdf_file_path

    def get_fecha_de_corte(self):
        return self.fecha_de_corte.strftime('%Y-%m-%d')

    def get_date_periodo_inicio(self):
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

    def get_human_readable_name(self) -> str:
        return (
            f"{self.get_bank_short_name()}_"
            f"{self.get_account_type_name()}__"
            f"{self.get_date_periodo_inicio()}__"
            f"{self.month_short_name}"
        )

    def get_unique_name(self) -> str:
        return (
            f"{self.get_bank_name()}__"
            f"{self.numero_de_cuenta}__"
            f"{self.get_date_periodo_inicio()}__"
            f"{self.get_periodo_termino()}"
        )

    def get_unique_file_id(self) -> str:
        return (
            f"{self.get_bank_name()}__"
            f"{self.get_date_periodo_inicio()}__"
            f"{self.get_periodo_termino()}__"
            f"corte__{self.get_fecha_de_corte()}__"
            f"size__{self.file_size}"
        )

    def auto_rename_file_name(self):
        new_file_name = f"{self.pdf_file_dir_name}/{self.get_human_readable_name()}.pdf"
        if not os.path.exists(new_file_name):
            if self.pdf_file_basename != new_file_name:
                print(f"[auto-rename] '{self.pdf_file_path}' -> '{new_file_name}'")
                os.rename(self.pdf_file_path, new_file_name)

    @classmethod
    def keywords_found_in_pdf_contents(cls, pdf_contents: str):
        for keyword in cls.PDF_KEYWORDS:
            if keyword in pdf_contents:
                return True
        return False

    @classmethod
    def format_date_period_string_into_datetime_tuple(cls, date_period_string):
        """
        Formats:
            '4 de febrero al 3 de marzo del 2024'
        """
        date_period_string = date_period_string.lower()

        # Replace ('al', 'de', 'del') with an empty string and remove leading/trailing spaces
        cleaned_date = date_period_string.replace('al', '').strip()
        cleaned_date = cleaned_date.replace('del', '').strip()
        cleaned_date = cleaned_date.replace('de', '').strip()
        cleaned_date = ' '.join(cleaned_date.split())

        year = cleaned_date.split()[-1]

        cleaned_date = cleaned_date.replace(year, '').strip()

        start_date_str = ' '.join(cleaned_date.split()[:2])
        end_date_str = ' '.join(cleaned_date.split()[-2:])

        start_date_str = f"{start_date_str} {year}"
        end_date_str = f"{end_date_str} {year}"

        # Create datetime objects
        start_date = cls.format_date_string_into_datetime(start_date_str)
        end_date = cls.format_date_string_into_datetime(end_date_str)

        return start_date, end_date

    @classmethod
    def format_date_string_into_datetime(cls, date_string):

        day = None
        month = None
        year = None

        split_by = ' '
        if 'de' in date_string:
            split_by = ' de '

        pattern_dd_al_dd_month_de_yyyy = r'^(\d{2})\s*al\s*(\d{2})\s*de\s*(\w+)+\s*de\s*(\d{4})$'
        pattern_dd_de_month_de_yyyy = r'^(\d{2})\s*de\s*(\w+)+\s*de\s*(\d{4})$'

        match_dd_al_dd_month_de_yyyy = re.match(pattern_dd_al_dd_month_de_yyyy, date_string.lower())
        match_dd_de_month_de_yyyy = re.match(pattern_dd_de_month_de_yyyy, date_string.lower())

        if match_dd_al_dd_month_de_yyyy:
            day = match_dd_al_dd_month_de_yyyy.group(1)
            month = match_dd_al_dd_month_de_yyyy.group(3)
            year = match_dd_al_dd_month_de_yyyy.group(4)
        elif match_dd_de_month_de_yyyy:
            day = match_dd_de_month_de_yyyy.group(1)
            month = match_dd_de_month_de_yyyy.group(2)
            year = match_dd_de_month_de_yyyy.group(3)
        else:
            # Split the input string
            day, month, year = date_string.split(split_by)

        # Convert month name to English
        month = cls._MONTH_MAPPING[month]

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
