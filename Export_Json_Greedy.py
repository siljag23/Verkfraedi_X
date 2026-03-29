import json

def Export_Json(dict_employees, dict_events, rows, month):

    # Búum til lista með pörum af EventID og EmployeeED
    pairs_for_json = [[row["EventID"], row["EmployeeID"]] for row in rows]

    # Aðlaga employee dicts fyrir json skjal
    keys_to_keep = ["EmployeeID", "EmployeeName", "Score", "Skillset"]
    filtered_employees = {}

    for emp_id, info in dict_employees.items():
        filtered_employees[emp_id] = {
            k: info[k]
            for k in keys_to_keep
            if k in info
        }

    # Aðlögum events og employees fyrir json skjal
    info_for_json = {
        "events": dict_events,
        "employees": filtered_employees
    }

    with open(f"{month}_output_list.json", "w", encoding = "utf-8") as f:
        json.dump(pairs_for_json, f, indent = 4, ensure_ascii = False)

    with open(f"{month}_output_dicts.json", "w", encoding = "utf-8") as f:
        json.dump(info_for_json, f, indent = 4, ensure_ascii = False, default = str)