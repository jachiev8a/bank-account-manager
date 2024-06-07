from banks.base_classes import BankAccountStatePDF


class SantanderBasePDF(BankAccountStatePDF):

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

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None):
        super().__init__(pdf_file_path, raw_file_contents)
        self.is_debit = True


class SantanderDebitPDF(SantanderBasePDF):
    pass


class SantanderDebitImagePDF(SantanderBasePDF):

    PATTERN_FECHA_DE_CORTE = r"CORTE\s{1}AL\s{1}(.*)"
    PATTERN_PERIODO = r"PERIODO\s{1}DEL\s{1}(.*)"

    PATTERN_NUMERO_DE_CUENTA = r"SUPERCUENTA\s{1}CHEQUES\-SALDO\s{1}PROM\s{1}(.*)"
    PATTERN_NUMERO_DE_CLIENTE = r"CODIGO\s{1}\nDE\s{1}\nCLIENTE\s{1}NO\.{1}(.*)"

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None):
        super().__init__(pdf_file_path, raw_file_contents)
        self.is_image_pdf = True
