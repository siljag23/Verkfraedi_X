from datetime import datetime, timedelta, time
from open_excel import shift_length

def pick_employees(dict_events, dict_employees, hours_per_employee, employee_days,
                   event_id: int, next_index: int):

    event = dict_events[event_id]
    n_employees = int(event["Employees"])

    #Pössum að date sé formattað sem date
    raw_date = event["Date"]
    if isinstance(raw_date, str):
        event_date = datetime.strptime(raw_date.strip(), "%d.%m.%Y").date()
    elif hasattr(raw_date, "date"):
        event_date = raw_date.date()
    else:
        event_date = raw_date

    start_dt = datetime.combine(event_date, event["ShiftBegins"])
    end_dt = datetime.combine(event_date, event["ShiftsEnds"])
    if end_dt < start_dt:
        end_dt += timedelta(days=1)

    blocked_days = {start_dt.date()}
    if end_dt.date() != start_dt.date() and end_dt.time() != time(0, 0):
        blocked_days.add(end_dt.date())

    #Röðum starfsmönnum í stafrófsröð
    sorted_employee_ids = [
        emp_id
        for emp_id, info in sorted(
            dict_employees.items(),
            key=lambda item: (item[1].get("EmployeeName", ""), item[0])
        )
    ]

    #Velja með round-robin, en sleppa þeim sem eru búnir að vinna sama dag
    chosen_ids = []
    N = len(sorted_employee_ids)
    i = next_index
    checked = 0

    while len(chosen_ids) < n_employees and checked < N:
        emp_id = sorted_employee_ids[i % N]
        i += 1
        checked += 1

        #Bönnum að vinna tvisvar sama dag
        if event_date in employee_days[emp_id]:
            continue

        chosen_ids.append(emp_id)

    #Starfsmenn mega ekki vinna meira en 13 klst. á sólarhring

    if len(chosen_ids) < n_employees:
        raise ValueError(
            f"Ekki nægur fjöldi af starfsmönnum laus (án tvöfaldra vakta sama dag): "
            f"þarf {n_employees}, en aðeins {len(chosen_ids)} eru lausir sem eru starfsmenn með ID: {chosen_ids}"
        )

    # Uppfæra next_index þannig röðin haldi áfram rétt
    next_index = i % N

    shift_hours = shift_length(event["ShiftBegins"], event["ShiftsEnds"])

    out = []
    for emp_id in chosen_ids:
        hours_per_employee[emp_id] += shift_hours
        employee_days[emp_id].add(event_date)
        out.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            "ShiftHours": shift_hours,
            "TotalHours": hours_per_employee[emp_id]
        })

    return out, next_index