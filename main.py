import webbrowser
from datetime import datetime
from pathlib import Path

import settings
from src.account_state_manager import PDFBankAccountStateManager
from src.report import build_report


def main():
    """Main function to execute the script.
    """
    directory_list = settings.get_directory_list_to_look_for_pdfs()
    bank_account_state_manager = PDFBankAccountStateManager()
    bank_account_state_manager.load_directories_to_search_for_pdfs(
        directory_list=directory_list,
    )
    bank_account_state_manager.list_bank_accounts_loaded(
        add_details=True,
        order_by="date",
    )
    bank_account_state_manager.build_output_project(
        start_clean=True,
    )

    statements = [
        s for s in bank_account_state_manager.bank_accounts_loaded.values()
        if bank_account_state_manager.is_bank_account_type_enabled(s)
    ]
    config_used = {
        "Generado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Carpetas": settings.get_directory_list_to_look_for_pdfs(),
        "Desde": settings.get_bank_account_after_date_config(),
        "Hasta": settings.get_bank_account_before_date_config(),
        "Tipos de cuenta": settings.get_bank_account_types_enabled_by_configuration(),
        # ponytail: shown but not applied yet (docs/future-work.md #2)
        "Bancos (aún no se aplica)": settings.get_configuration_data().get("bank_names_enabled", []),
        "Log level": settings.get_log_level(),
    }
    report_path = build_report(
        statements,
        bank_account_state_manager.failed_files,
        f"{settings.get_tmp_dir()}/report.html",
        config=config_used,
    )
    print(f"Report: {report_path}")
    webbrowser.open(Path(report_path).as_uri())


# =============================================================
# Main Entry point for the script
# =============================================================
if __name__ == "__main__":
    main()
