
import random

def pick_employees(dict_events, dict_employees, event_id:int):

    event = dict_events[event_id]
    n = int(event["Employees"])

    employee_ids = list(dict_employees.keys())
    if n > len(employee_ids):
        raise ValueError(f"Ekki nóg af starfsmönnum: þarf {n}, en eru {len(employee_ids)}")

    chosen_ids = random.sample(employee_ids, n)

    # skila lista af pörum: (EventID, EmployeeID, EmployeeName)
    out = []
    for emp_id in chosen_ids:
        out.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName")
        })
    return out



