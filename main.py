import settings
from src.account_state_manager import PDFBankAccountStateManager


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


# =============================================================
# Main Entry point for the script
# =============================================================
if __name__ == "__main__":
    main()
