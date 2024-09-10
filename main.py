import settings
from banks.account_state_manager import PDFBankAccountStateManager

DIR_LIST_TO_LOOK_FOR_PDFS = (
    settings.get_directory_list_to_look_for_pdfs()
)


bank_account_state_manager = PDFBankAccountStateManager()
bank_account_state_manager.load_directories_to_search_for_pdfs(
    directory_list=DIR_LIST_TO_LOOK_FOR_PDFS,
)

bank_account_state_manager.auto_rename_bank_accounts_loaded()
bank_account_state_manager.list_bank_accounts_loaded(
    add_details=True,
    order_by="date",
)
bank_account_state_manager.build_output_project(
    start_clean=True,
)

a = 0
