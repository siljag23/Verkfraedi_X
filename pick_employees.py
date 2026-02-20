from open_excel import shift_length

# Fall sem velur hvaða starfsmaður fær næstu vakt
def pick_employees(dict_events, dict_employees, hours_per_employee, employee_days,
                   event_id: int, next_index: int):

    event = dict_events[event_id]
    n_employees = int(event["Employees"])

    #Finnum dagsetningu viðburðar
    shift_begins = event["ShiftBegins"]
    # Ef ShiftBegins er datetime -> .date()
    if hasattr(shift_begins, "date"):
        event_date = shift_begins.date()
    else:
        # Fallback: ef ShiftBegins er strengur, notum fyrstu 10 stafi (t.d. 'YYYY-MM-DD')
        # Aðlagaðu þetta ef sniðið þitt er öðruvísi
        event_date = str(shift_begins)[:10]

    # --- Starfsmenn í stafrófsröð, EN sleppum þeim sem eru þegar á vakt sama dag ---
    eligible_employee_ids = [
        emp_id for emp_id, info in sorted(
            dict_employees.items(),
            key=lambda item: (item[1].get("EmployeeName", ""), item[0])
        )
        if event_date not in employee_days[emp_id]
    ]

    if n_employees > len(eligible_employee_ids):
        raise ValueError(
            f"Ekki nægur fjöldi af starfsmönnum laus (án tvöfaldra vakta sama dag): "
            f"fyrir viðburðinn þarf {n_employees} starfsmenn, en það eru {len(eligible_employee_ids)} lausir"
        )

    # --- Round-robin val á eligible listanum ---
    chosen_ids = []
    for _ in range(n_employees):
        chosen_ids.append(eligible_employee_ids[next_index % len(eligible_employee_ids)])
        next_index += 1

    shift_hours = shift_length(event["ShiftBegins"], event["ShiftsEnds"])

    # --- Skila út og uppfæra bæði klst og daga ---
    out = []
    for emp_id in chosen_ids:
        hours_per_employee[emp_id] += shift_hours
        employee_days[emp_id].add(event_date)  # <-- bannar fleiri en eina vakt sama dag
        out.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            "ShiftHours": shift_hours,
            "TotalHours": hours_per_employee[emp_id]
        })

    return out, next_index
