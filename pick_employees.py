from datetime import datetime, timedelta
from open_excel import shift_length

def pick_employees(dict_events, dict_employees, hours_per_employee, employee_days,
                   event_id: int, next_index: int):

    event = dict_events[event_id]
    n_employees = int(event["Employees"])

    #Sækjum dagsetningu á viðburðum
    event_date = event["Date"]

    #Ef Date kemur sem strengur (t.d. "1.5.2024") breytum í datetime.date
    if isinstance(event_date, str):
        event_date = datetime.strptime(event_date, "%d.%m.%Y").date()
    elif hasattr(event_date, "date"):
        event_date = event_date.date()

    start_dt = datetime.combine(event_date, event["ShiftBegins"])
    end_dt = datetime.combine(event_date, event["ShiftsEnds"])

    if end_dt < start_dt:
        end_dt += timedelta(days=1)

    #Dagurinn sem vaktin byrjar
    event_day_key = start_dt.date()

    #Röðum starfsmönnum í stafrófsröð
    sorted_employee_ids = [
        emp_id
        for emp_id, info in sorted(
            dict_employees.items(),
            key=lambda item: (item[1].get("EmployeeName", ""), item[0])
        )
    ]

    #Sleppum þeim sem eru þegar á vakt þennan dag
    eligible_employee_ids = [
        emp_id for emp_id in sorted_employee_ids
        if event_day_key not in employee_days[emp_id]
    ]

    if n_employees > len(eligible_employee_ids):
        raise ValueError(
            f"Ekki nægur fjöldi af starfsmönnum laus "
            f"(án tvöfaldra vakta sama dag): þarf {n_employees}, "
            f"en {len(eligible_employee_ids)} eru lausir"
        )

    chosen_ids = []
    for _ in range(n_employees):
        chosen_ids.append(
            eligible_employee_ids[next_index % len(eligible_employee_ids)]
        )
        next_index += 1

    shift_hours = shift_length(event["ShiftBegins"], event["ShiftsEnds"])

    out = []
    for emp_id in chosen_ids:
        hours_per_employee[emp_id] += shift_hours
        employee_days[emp_id].add(event_day_key)  #Bannar fleiri en eina vakt sama dag
        out.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            "ShiftHours": shift_hours,
            "TotalHours": hours_per_employee[emp_id]
        })

    return out, next_index