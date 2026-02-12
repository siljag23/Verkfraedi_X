
import random
from open_excel import shift_length



def pick_employees(dict_events, dict_employees, hours_per_employee, event_id:int):

    event = dict_events[event_id]
    n = int(event["Employees"])


    employee_ids = list(dict_employees.keys())
    if n > len(employee_ids):
        raise ValueError(f"Ekki nóg af starfsmönnum: þarf {n}, en eru {len(employee_ids)}")

    chosen_ids = random.sample(employee_ids, n)

    shift_hours = shift_length(event["Shift begins"], event["Shifts ends"])
    ranked = sorted(
        employee_ids,
        key=lambda emp_id: (hours_per_employee[emp_id], random.random())
    )

    chosen_ids = ranked[:n]
    
    # skila lista af pörum: (EventID, EmployeeID, EmployeeName)
    out = []
    for emp_id in chosen_ids:
        hours_per_employee[emp_id] += shift_hours
        out.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            "TotalHours": hours_per_employee[emp_id]
        })
    return out



