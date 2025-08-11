from src.banks.base_classes import BankAccountStatePDF


class BanamexDebitPDF(BankAccountStatePDF):

    BANK_NAME = "banamex"
    BANK_SHORT_NAME = "banamex"
    PDF_KEYWORDS = [
        "banamex.com",
        # "www.banamex.com",
    ]
    PATTERN_FECHA_DE_CORTE = r"Fecha de Corte\s?[\w]?\n+(.*)"
    PATTERN_PERIODO = r"Período del (.*)"

    PATTERN_NUMERO_DE_CUENTA = r"Número de cuenta de cheques\n+(.*)"
    PATTERN_NUMERO_DE_CLIENTE = r"Número de cliente\n+(.*)"
    PATTERN_NUMERO_DE_TARJETA = None

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None):
        super().__init__(pdf_file_path, raw_file_contents)
        self.is_debit = True


class BanamexCreditCostco2025FormatPDF(BankAccountStatePDF):

    BANK_NAME = "banamex"
    BANK_SHORT_NAME = "banamex"
    PDF_KEYWORDS = [
        "COSTCO",
        # this is a table title available on the new format
        "TU PAGO REQUERIDO ESTE PERIODO"
    ]
    ALL_KEYWORDS_SHOULD_BE_IN_PDF = True
    # Fecha de corte:\n16-dic-2024
    PATTERN_FECHA_DE_CORTE = r"Fecha de corte:\n?\s*(\d{2}-\w{3}-\d{4})"
    # Periodo:\n\s16-nov-2024 al 16-dic-2024
    PATTERN_PERIODO = r"Periodo:\n?\s*(\d{2}-\w{3}-\d{4} al \d{2}-\w{3}-\d{4})"

    PATTERN_NUMERO_DE_CUENTA = r"Número de cuenta de cheques\n+(.*)"
    PATTERN_NUMERO_DE_CLIENTE = r"Número de cliente\n+(.*)"
    PATTERN_NUMERO_DE_TARJETA = r"Número de tarjeta\n+(.*)"

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None):
        super().__init__(pdf_file_path, raw_file_contents)
        self.is_credit = True

