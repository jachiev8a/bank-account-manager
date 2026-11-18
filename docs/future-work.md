# Future Work

Known bugs found by code review (static reading, not run against real PDFs).

## Worth deciding

### 2. `bank_names_enabled` config is never read
- **Where:** `config.yaml` / `settings.py`
- **Problem:** No code reads this key. Commenting out a bank has no effect, and banks not
  listed (Santander, Inbursa, Banamex) are still processed.
- **Fix idea:** Add a getter in `settings.py` and filter in the manager, or remove the key.

### 3. Citibanamex credit classes are unused
- **Where:** `src/banks/citibanamex.py` — `CitiBanamexCreditCostcoPDF`,
  `CitiBanamexCreditCostco2025FormatPDF`
- **Problem:** Not imported or wired into `build_bank_account_state_object_from_pdf_file`.
  The 2025 format seems superseded by `BanamexCreditCostco2025FormatPDF`, but old-format
  Citibanamex Costco statements (2024) are not detected at all.
- **Fix idea:** Wire `CitiBanamexCreditCostcoPDF` into the detection chain if those PDFs
  matter; delete the 2025 duplicate.

### Santander account-number regex grabs the wrong digits
- **Where:** `src/banks/santander.py` — `PATTERN_NUMERO_DE_CUENTA` (text and image variants)
- **Problem:** Captures the line after "SUPERCUENTA CHEQUES-SALDO PROM", which holds other
  figures (likely the average balance), so the report's last 4 digits change per statement.
- **Workaround:** `SPLIT_REPORT_BY_NUMBER = False` in `BankAccountStatePDF` (all banks), so the
  report groups by bank + type only.
- **Fix idea:** Rewrite the regex using a masked sample of that line; verify the other banks'
  number regexes too, then set `SPLIT_REPORT_BY_NUMBER = True` per bank that's verified.

## Cleanup

### 4. Raw contents fallback is overwritten
- **Where:** `src/banks/base_classes.py`, `BankAccountStatePDF.__init__` (~line 198-200)
- **Problem:** Missing `else`: `self.raw_pdf_file_contents = raw_file_contents` always runs,
  overwriting the loaded contents with `None`. Harmless today since every caller passes contents.

### 5. `get_fecha_de_corte(month_as_name=True)` is a no-op
- **Where:** `src/banks/base_classes.py`, `get_fecha_de_corte`
- **Problem:** Result of the `strftime` is discarded, and `%M` is minutes, not month.
  No caller uses the flag — delete it or implement it.

### 6. Unknown-bank branch is a stub
- **Where:** `src/account_state_manager.py`, `build_bank_account_state_object_from_pdf_file`
- **Problem:** `elif UnknownBankAccountStatePDF...: a = 0` — unrecognized PDFs are silently skipped.
- **Fix idea:** Log the skipped file so new formats are noticed.

## Report (`src/report.py`)

- Month = `periodo_inicio` month (same as file naming). Revisit: credit cards may read
  better by `fecha_de_corte` month.
- Accounts split by last 4 digits of card/account number. If OCR misreads them, a statement
  shows up as its own one-month account; fallback is grouping by bank + type only.
- Next iteration (if wanted): local web server with re-scan button / notes per month.
