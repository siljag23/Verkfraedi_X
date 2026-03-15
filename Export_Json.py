import json

def Export_Json(dict_events, dict_employees, works, employees, events):

    output_dicts = {
        "events": dict_events,
        "employees": dict_employees
    }

    with open("05_24_optioutput_dicts.json", "w", encoding="utf-8") as f:
        json.dump(output_dicts, f, indent=4, ensure_ascii=False, default=str)

    assignment_list = []

    for j in events:
        for i in employees:
            if works[i, j].X > 0.5:
                assignment_list.append([j, i])

    with open("05_24_optioutput_list.json", "w", encoding="utf-8") as f:
        json.dump(assignment_list, f, indent=4)