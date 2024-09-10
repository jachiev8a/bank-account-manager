import json


class ReportManager:
    def __init__(self):
        pass

    def generate_json_report(self, report_data: dict, report_file_path: str):
        with open(report_file_path, "w") as f_obj:
            json.dump(report_data, f_obj, indent=4)
