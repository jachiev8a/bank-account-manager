from banks.base_classes import BankAccountStatePDF


# class BbvaGenericPDF(BankAccountStatePDF):
#
#     BANK_NAME = "bbva"
#     BANK_SHORT_NAME = "bbva"
#     PDF_KEYWORDS = [
#         "BBVA",
#         "bbva",
#     ]
#
#     PATTERN_FECHA_DE_CORTE = r"Fecha de [Cc]orte:?\s?\n+(.*)"
#     PATTERN_PERIODO = r"Periodo:?\s?\n+D?E?L?\s?(.*)"
#
#     PATTERN_NUMERO_DE_CUENTA = r"(Número|No.) de (Cuenta|cliente):\s?\n?(.*)"
#     PATTERN_NUMERO_DE_CLIENTE = r"Número de cliente:\s?(.*)"
#     PATTERN_NUMERO_DE_TARJETA = r"Número de tarjeta:\s?(.*)"
#
#     MAX_LIMIT_TO_SEARCH_FOR_KEYWORDS = 100
#
#     def __init__(self, pdf_file_path: str, raw_file_contents: str = None):
#         super().__init__(pdf_file_path, raw_file_contents)
#         self.is_debit = True


class BbvaDebitPDF(BankAccountStatePDF):

    BANK_NAME = "bbva"
    BANK_SHORT_NAME = "bbva"
    PDF_KEYWORDS = [
        "BBVA",
        "NOMINA",
    ]

    ALL_KEYWORDS_SHOULD_BE_IN_PDF = True

    PATTERN_FECHA_DE_CORTE = r"Fecha de Corte\s?\n+(.*)"
    PATTERN_PERIODO = r"Periodo\s?\n+DEL\s?(.*)"

    PATTERN_NUMERO_DE_CUENTA = r"No. de Cuenta\s?\n+(.*)"
    PATTERN_NUMERO_DE_CLIENTE = r"No. de Cliente\s?\n+(.*)"
    PATTERN_NUMERO_DE_TARJETA = None

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None):
        super().__init__(pdf_file_path, raw_file_contents)
        self.is_debit = True


class BbvaCreditPDF(BankAccountStatePDF):

    BANK_NAME = "bbva"
    BANK_SHORT_NAME = "bbva"
    PDF_KEYWORDS = [
        "BBVA",
        "Pago para no generar intereses",
    ]

    ALL_KEYWORDS_SHOULD_BE_IN_PDF = True

    PATTERN_FECHA_DE_CORTE = r"Fecha de corte:\s?\n+(.*)"
    PATTERN_PERIODO = r"Periodo:\s?\n+(.*)"

    PATTERN_NUMERO_DE_CUENTA = r"Número de cliente:\s?(.*)"
    PATTERN_NUMERO_DE_CLIENTE = r"Número de cliente:\s?(.*)"
    PATTERN_NUMERO_DE_TARJETA = r"Número de tarjeta:\s?(.*)"

    def __init__(self, pdf_file_path: str, raw_file_contents: str = None):
        super().__init__(pdf_file_path, raw_file_contents)
        self.is_credit = True
