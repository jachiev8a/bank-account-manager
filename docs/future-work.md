# Future Work

Known bugs found by code review (static reading, not run against real PDFs).

## Priority

### 1. One bad PDF aborts the whole run
- **Where:** `src/banks/base_classes.py` — `_validate_fields` raises `RuntimeError` when
  `fecha_de_corte` / `periodo_*` are missing; `get_regex_pattern_from_date_string` raises
  `RuntimeError` for unsupported date formats.
- **Problem:** Nothing in `src/` or `main.py` catches these. A single badly OCR'd or
  new-format PDF stops processing of every file after it. Files already auto-renamed stay renamed.
- **Fix idea:** Catch per-file in `PDFBankAccountStateManager.load_directories_to_search_for_pdfs`,
  log the file + reason, and continue.

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

## Missing feature

### Missing-months report
The original goal (detect which monthly statements are missing) is not implemented.
The data is already there (`periodo_inicio`, bank, account type); needs a step that lists,
per bank + account type, months with no statement between the first and last one found
(or a configured range).
