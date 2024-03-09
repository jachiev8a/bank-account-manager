import re
from banks.base_classes import BankPDF


class CitiBanamexPDF(BankPDF):

    PDF_KEYWORDS = [
        "Citibanamex",
        "citibanamex",
    ]
    PATTERN_FECHA_DE_CORTE = r"Fecha de Corte\s?[\w]?\n+(.*)"
    PATTERN_NUMERO_DE_CUENTA = r"Número de cuenta de cheques\n+(.*)"
    PATTERN_NUMERO_DE_CLIENTE = r"Número de cliente\n+(.*)"
    PATTERN_PERIODO = r"Período del (.*)"

    def __init__(self, pdf_file_path):
        super().__init__(pdf_file_path)
        self.load_bank_data_from_pdf()

    def load_bank_data_from_pdf(self):

        # Use re.search to find the pattern in the text
        match_fecha_corte = re.search(
            self.PATTERN_FECHA_DE_CORTE,
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

        match_periodo = re.search(
            self.PATTERN_PERIODO,
            self.raw_pdf_file_contents
        )

        if match_fecha_corte:
            fecha_de_corte = match_fecha_corte.group(1)
            self.raw_data["fecha_de_corte"] = fecha_de_corte
            self.fecha_de_corte = self.format_date_string_into_datetime(fecha_de_corte)

        if match_numero_de_cuenta:
            self.numero_de_cuenta = match_numero_de_cuenta.group(1)

        if match_numero_cliente:
            self.numero_de_cliente = match_numero_cliente.group(1)

        if match_periodo:
            periodo = match_periodo.group(1)
            self.raw_data["periodo"] = periodo
            self.periodo = self.format_date_period_string_into_datetime_tuple(periodo)


    def get_fecha_de_corte(self):
        print("NOT IMPLEMENTED")

    @classmethod
    def keywords_found_in_pdf_contents(cls, pdf_contents: str):
        for keyword in cls.PDF_KEYWORDS:
            if keyword in pdf_contents:
                return True
        return False
