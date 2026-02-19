from open_excel import shift_length

# Fall sem velur hvaða starfsmaður fær næstu vakt

def pick_employees(dict_events, dict_employees, hours_per_employee, event_id:int, next_index):

    #n_employees er fjöldi starfsmanna sem þarf á hverja vakt

    event = dict_events[event_id]
    n_employees = int(event["Employees"])

    #röðum starfsmönnum eftir stafsrófsröð

    sorted_employee_ids = [
        emp_id
        for emp_id, info in sorted(
            dict_employees.items(),
            key = lambda item: (item[1].get("EmployeeName",""), item[0])
        )
    ]

    if n_employees > len(sorted_employee_ids):
        raise ValueError(f"Ekki nægur fjöldi af starfsmönnum laus: fyrir viðburðinn þarf {n} starfsmenn, en það eru {len(employee_ids)} lausir")

    chosen_ids = []
    for i in range(n_employees):
        chosen_ids.append(sorted_employee_ids[next_index % len(sorted_employee_ids)])
        next_index += 1

    shift_hours = shift_length(event["ShiftBegins"], event["ShiftsEnds"])
    
    # skila lista af pörum: (EventID, EmployeeID, EmployeeName)
    out = []
    for emp_id in chosen_ids:
        hours_per_employee[emp_id] += shift_hours
        out.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            "ShiftHours": shift_hours,
            "TotalHours": hours_per_employee[emp_id]
        })
    """
    print(out)
    print("")
    print(next_index)
    """
    return out, next_index