import locale
from abc import ABC, abstractmethod
from datetime import datetime

from pdf_utils.parsers import parse_pdf_with_pymupdf


class BankPDF(ABC):

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

    def __init__(self, pdf_file_path):
        self.pdf_file_path = pdf_file_path
        self.raw_pdf_file_contents = self._load_raw_pdf_file_contents()

        self.raw_data = {}

        self.fecha_de_corte = None
        self.periodo = None
        self.numero_de_cuenta = None
        self.numero_de_cliente = None

    def _load_raw_pdf_file_contents(self):
        file_contents = parse_pdf_with_pymupdf(self.pdf_file_path)
        return file_contents

    def get_pdf_file_path(self):
        return self.pdf_file_path

    @classmethod
    def format_date_period_string_into_datetime_tuple(cls, date_period_string):
        # Replace "al" with an empty string and remove leading/trailing spaces
        cleaned_date = date_period_string.replace('al', '').strip()
        cleaned_date = cleaned_date.replace('del', '').strip()

        year = cleaned_date.split()[-1]

        # Split the date into start and end parts
        start_date_str, end_date_str, year = cleaned_date.split(' de ')

        # Convert month names to English
        start_month = cls._MONTH_MAPPING[start_date_str.split()[1]]
        end_month = cls._MONTH_MAPPING[end_date_str.split()[1]]

        # Create datetime objects
        start_date = datetime.strptime(f"{start_date_str} {year}", "%d %B %Y")
        end_date = datetime.strptime(f"{end_date_str} {year}", "%d %B %Y")

        # Reset the locale to the default value
        locale.setlocale(locale.LC_TIME, '')

        return start_date, end_date

    @classmethod
    def format_date_string_into_datetime(cls, date_string):
        # Split the input string
        day, month, year = date_string.split(' de ')

        # Convert month name to English
        month = cls._MONTH_MAPPING[month]

        # Create datetime object
        date_string = f"{day} {month} {year}"
        datetime_object = datetime.strptime(date_string, "%d %B %Y")

        return datetime_object

    @classmethod
    def format_datetime_into_standard(cls, datetime_date: datetime):
        return datetime_date.strftime("%y-%m-%d")

    @abstractmethod
    def load_bank_data_from_pdf(self):
        pass

    @abstractmethod
    def get_fecha_de_corte(self):
        pass
