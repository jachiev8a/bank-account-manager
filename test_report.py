"""Self-check for the missing-months report with fake statements (no PDFs).
Run: python test_report.py
"""
import tempfile
from datetime import datetime
from pathlib import Path

from src.report import build_report, find_gaps, group_by_account


class Fake:
    def __init__(self, bank, kind, date, tarjeta=None, cuenta=None):
        self.periodo_inicio = datetime.strptime(date, "%Y-%m-%d")
        self.numero_de_tarjeta, self.numero_de_cuenta = tarjeta, cuenta
        self._bank, self._kind, self._date = bank, kind, date
        self.output_file_path = f"/tmp-copy/{bank}/{kind}/{date}.pdf"

    def get_bank_name(self): return self._bank
    def get_account_type_name(self): return self._kind
    def get_pdf_file_path(self): return f"/x/{self._bank}_{self._kind}__{self._date}.pdf"


statements = [
    # user's example: SEP and NOV present -> OCT missing
    Fake("bbva", "credito", "2024-09-16", tarjeta="4152 3100 0000 1234"),
    Fake("bbva", "credito", "2024-11-16", tarjeta="4152 3100 0000 1234"),
    # Dec -> Feb across the year boundary -> Jan missing
    Fake("santander", "debito", "2024-12-01", cuenta="65-00000-5678"),
    Fake("santander", "debito", "2025-02-01", cuenta="65-00000-5678"),
    # two PDFs in the same month
    Fake("santander", "debito", "2025-02-15", cuenta="65-00000-5678"),
    # second BBVA card -> separate account
    Fake("bbva", "credito", "2024-10-16", tarjeta="4152 3100 0000 9999"),
]

# bank with unreliable numbers: different digits still group as one account
class NoSplit(Fake):
    SPLIT_REPORT_BY_NUMBER = False

statements += [
    NoSplit("santander_img", "debito", "2024-01-01", cuenta="9820"),
    NoSplit("santander_img", "debito", "2024-02-01", cuenta="1534"),
]

accounts = group_by_account(statements)
assert set(accounts) == {
    ("bbva", "credito", "1234"),
    ("bbva", "credito", "9999"),
    ("santander", "debito", "5678"),
    ("santander_img", "debito", None),
}
assert find_gaps(accounts[("bbva", "credito", "1234")]) == [(2024, 10)]
assert find_gaps(accounts[("santander", "debito", "5678")]) == [(2025, 1)]
assert find_gaps(accounts[("bbva", "credito", "9999")]) == []
assert len(accounts[("santander", "debito", "5678")][(2025, 2)]) == 2

with tempfile.TemporaryDirectory() as tmp:
    out = build_report(statements, [("/x/broken.pdf", "bad date")], f"{tmp}/r.html")
    page = Path(out).read_text()
    assert "<b>2</b><span>Meses faltantes" in page
    assert "OCT 2024" in page and "ENE 2025" in page
    assert page.count('target="_blank"') == 8  # every statement opens its PDF
    assert page.count('href="file:///tmp-copy/') == 8  # ...from the .tmp copy
    assert "····1234" in page and "3100 0000" not in page  # only last 4 digits
    assert "broken.pdf" in page and "×2" in page

print("ok")
