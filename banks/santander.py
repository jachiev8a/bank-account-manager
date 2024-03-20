from banks.base_classes import BankAccountStatePDF


class SantanderDebitPDF(BankAccountStatePDF):

    BANK_NAME = "santander"
    BANK_SHORT_NAME = "santander"
    PDF_KEYWORDS = [
        "Santander",
        "santander",
    ]
    PATTERN_FECHA_DE_CORTE = r"PERIODO\s+\:\s+\d{2}\s+AL\s+(.*)"
    PATTERN_PERIODO = r"PERIODO\s+\:\s+(.*)"

    PATTERN_NUMERO_DE_CUENTA = r"SUPERCUENTA\s+CHEQUES\-SALDO\s+PROM\n+(.*)"
    PATTERN_NUMERO_DE_CLIENTE = r"CODIGO\s*\nDE\s*\nCLIENTE\s*\nNO\.\s*\n(.*)"
    PATTERN_NUMERO_DE_TARJETA = None

    def __init__(self, pdf_file_path):
        super().__init__(pdf_file_path)
        self.is_debit = True
