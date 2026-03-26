import json

def Export_Json(dict_events, dict_employees, works, employees, events, base_filename):

    dict_output = {
        "events": dict_events,
        "employees": dict_employees
    }

    dict_filename = f"{base_filename}_dicts.json"

    with open(dict_filename, "w", encoding="utf-8") as f:
        json.dump(dict_output, f, indent=4, ensure_ascii=False, default=str)

    assignment_list = []

    for j in events:
        for i in employees:
            if works[i, j].X > 0.5:
                assignment_list.append([j, i])

    list_filename = f"{base_filename}_list.json"

    with open(list_filename, "w", encoding="utf-8") as f:
        json.dump(assignment_list, f, indent=4)

    print(f"Saved: {dict_filename}")
    print(f"Saved: {list_filename}")