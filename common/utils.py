import os
import json


def convert_bytes_to_human_readable(bytes_number):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    index = 0
    while bytes_number >= 1024 and index < len(suffixes) - 1:
        bytes_number /= 1024
        index += 1
    return f"{bytes_number:.0f} {suffixes[index]}"


def get_project_tmp_dir():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_tmp_dir = os.path.join(root_dir, "tmp")
    os.makedirs(project_tmp_dir, exist_ok=True)
    return project_tmp_dir


def write_json_file(json_file_path, data):
    with open(json_file_path, "w") as json_file_obj:
        json.dump(data, json_file_obj, indent=4)


def load_json_file(json_file_path) -> dict:
    if not os.path.exists(json_file_path):
        return {}
    with open(json_file_path, "r") as json_file_obj:
        json_data = json.load(json_file_obj)
    return json_data


def read_txt_file(file_path):
    with open(file_path, "r") as file_obj:
        file_contents = file_obj.read()
    return file_contents
