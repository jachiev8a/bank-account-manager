from banks.base_classes import BankAccountStatePDF


class InbursaDebitPDF(BankAccountStatePDF):

    BANK_NAME = "inbursa"
    BANK_SHORT_NAME = "inbursa"
    PDF_KEYWORDS = [
        "Inbursa",
        "inbursa",
        "INBURSA",
    ]
    PATTERN_FECHA_DE_CORTE = r"FECHA DE CORTE\n+(.*)"
    PATTERN_PERIODO = r"PERIODO\s?\n+Del\s(.*)"

    PATTERN_NUMERO_DE_CUENTA = r"CUENTA\n+(.*)"
    PATTERN_NUMERO_DE_CLIENTE = r"Cliente Inbursa: (.*)"
    PATTERN_NUMERO_DE_TARJETA = None

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None):
        super().__init__(pdf_file_path, raw_file_contents)
        self.is_debit = True
