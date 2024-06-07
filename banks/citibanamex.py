from banks.base_classes import BankAccountStatePDF


class CitiBanamexDebitPDF(BankAccountStatePDF):

    BANK_NAME = "citibanamex"
    BANK_SHORT_NAME = "citi"
    PDF_KEYWORDS = [
        "Citibanamex",
        "citibanamex",
    ]
    PATTERN_FECHA_DE_CORTE = r"Fecha de Corte\s?[\w]?\n+(.*)"
    PATTERN_PERIODO = r"Período del (.*)"

    PATTERN_NUMERO_DE_CUENTA = r"Número de cuenta de cheques\n+(.*)"
    PATTERN_NUMERO_DE_CLIENTE = r"Número de cliente\n+(.*)"
    PATTERN_NUMERO_DE_TARJETA = None

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None):
        super().__init__(pdf_file_path, raw_file_contents)
        self.is_debit = True


class CitiBanamexCreditCostcoPDF(BankAccountStatePDF):

    BANK_NAME = "citibanamex"
    BANK_SHORT_NAME = "citi"
    PDF_KEYWORDS = [
        "Costco",
        "COSTCO",
    ]
    # con fecha de corte al 16 de enero de 2024.
    PATTERN_FECHA_DE_CORTE = r"con fecha de corte al ([\w\s]*)"
    PATTERN_PERIODO = r"Del ([\w\s]*),"

    PATTERN_NUMERO_DE_CUENTA = r"Número de cuenta de cheques\n+(.*)"
    PATTERN_NUMERO_DE_CLIENTE = r"Número de cliente\n+(.*)"
    PATTERN_NUMERO_DE_TARJETA = r"NÚMERO DE TARJETA\n+(.*)"

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None):
        super().__init__(pdf_file_path, raw_file_contents)
        self.is_credit = True
