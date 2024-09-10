import os
import datetime

import yaml
from pathlib import Path

TMP_DIR_NAME = ".tmp"
CONFIGURATION_DATA = None


def get_project_root_dir():
    """
    Retrieves the project root dir, which is at:
        "{PROJECT}/flows"
    """
    return str(Path(__file__).resolve().parent)


def get_configuration_data() -> dict:
    global CONFIGURATION_DATA
    if CONFIGURATION_DATA is not None:
        return CONFIGURATION_DATA
    with open(f"{get_project_root_dir()}/config.yaml", "r") as f:
        try:
            CONFIGURATION_DATA = yaml.safe_load(f)
            return CONFIGURATION_DATA
        except yaml.YAMLError as exc:
            print(exc)


def get_directory_list_to_look_for_pdfs() -> list:
    config_data = get_configuration_data()
    return config_data.get("directory_list_to_look_for_pdfs", [])


def get_bank_account_after_date_config() -> datetime.date:
    config_data = get_configuration_data()
    after_date_value = config_data.get("get_bank_accounts_after_date", None)
    if after_date_value:
        return after_date_value
    else:
        return datetime.date(2000, 1, 1)


def get_tmp_dir():
    tmp_dir_path = f"{get_project_root_dir()}/{TMP_DIR_NAME}"
    os.makedirs(tmp_dir_path, exist_ok=True)
    return tmp_dir_path


def get_log_level() -> str:
    config_data = get_configuration_data()
    return config_data.get("log_level", "INFO")
