import json
from pathlib import Path

print("EXPORT_JSON FILE LOADED")
def Export_Json(dict_employees, dict_events, rows, month):
    print("EXPORT_JSON CALLED")
    """Export info for current scheduling period to 2 json files"""
    base_path = Path(__file__).resolve().parent

    output_list_path = Path("Data") / f"{month}_output_list.json"
    output_dict_path = Path("Data") / f"{month}_output_dicts.json"

    pairs_for_json = [[row["EventID"], row["EmployeeID"]] for row in rows]

    keys_to_keep = ["EmployeeID", "EmployeeName", "Skillset", "Availability_ratio"]
    filtered_employees = {}

    for emp_id, info in dict_employees.items():
        filtered_employees[emp_id] = {
            k: info[k]
            for k in keys_to_keep
            if k in info
        }
        filtered_employees[emp_id]["Score"] = info.get("score_added_this_period", 0)
 
    info_for_json = {
        "events": dict_events,
        "employees": filtered_employees
    }

    with open(output_list_path, "w", encoding="utf-8") as f:
        json.dump(pairs_for_json, f, indent=4, ensure_ascii=False)

    with open(output_dict_path, "w", encoding="utf-8") as f:
        json.dump(info_for_json, f, indent=4, ensure_ascii=False, default=str)