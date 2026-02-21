from datetime import datetime, timedelta, time
from shift_length import shift_length

def pick_employees(dict_events, dict_employees, hours_per_employee, employee_days, event_id: int, next_index: int):

    # Gera dict um einstaka viðburð úr dict af öllum viðburðum
    event = dict_events[event_id]

    # Sækja starfsmannaþörf fyrir viðburð
    req_employees = int(event["Employees"])

    # Sækja dagsetningu viðburðar og passa hún sé með rétt date format
    raw_date = event["Date"]
    
    if isinstance(raw_date, str):
        event_date = datetime.strptime(raw_date.strip(), "%d.%m.%Y").date()
    elif hasattr(raw_date, "date"):
        event_date = raw_date.date()
    else:
        event_date = raw_date

    # Upphafsstillum tíma hvenær vakt byrjar og endar, tími er dagur + klukka
    shift_begins = datetime.combine(event_date, event["ShiftBegins"])
    shift_ends = datetime.combine(event_date, event["ShiftsEnds"])

    # Breyta dagsetningu á shifts_end ef vakt fer yfir miðnætti
    if shift_ends < shift_begins:
        shift_ends += timedelta(days=1)

    # Ef þú ert með vakt á ákveðnum degi getur þú ekki fengið aðra vakt á þeim degi
    blocked_days = {shift_begins.date()}
    """
    # Þurfum ekki... held ég - Kata
    if shift_ends.date() != shift_begins.date() and shift_ends.time() != time(0, 0):
        blocked_days.add(shift_ends.date())
    """

    # Raða starfsmönnum í stafrófsröð, ef starfsmenn heita það saman þá raða eftir ID
    sorted_employee_ids = [
        emp_id
        for emp_id, info in sorted(
            dict_employees.items(),
            key=lambda item: (item[1].get("EmployeeName", ""), item[0])
        )
    ]

    # Velja starfsmenn með round-robin eftir starfrófsröð
    # Sleppa þeim sem eru búnir að vinna sama dag
    selected_employee_ids = []
    total_employees = len(sorted_employee_ids)
    i = next_index
    employees_checked = 0

    while len(selected_employee_ids) < req_employees and employees_checked < total_employees:
        emp_id = sorted_employee_ids[i % total_employees]
        i += 1
        employees_checked += 1

        # Skoða hvort dagsetning viburðar sé laus hjá starfsmanni
        # Hoppa yfir starfsmann ef hann er ekki laus (continue)
        if event_date in employee_days[emp_id]:
            continue

        selected_employee_ids.append(emp_id)

    # Starfsmenn mega ekki vinna meira en 13 klst. á sólarhring
    if len(selected_employee_ids) < req_employees:
        raise ValueError(
            f"Ekki nægur fjöldi af starfsmönnum laus þennan dag"
            f"Þarf {req_employees} starfsmenn en aðeins {len(selected_employee_ids)} eru lausir sem eru starfsmenn með ID: {selected_employee_ids}"
        )

    # Uppfæra next_index þannig röðin haldi áfram rétt
    next_index = i % total_employees

    # Reikna hvað vakt er löng
    shift_hours = shift_length(event["ShiftBegins"], event["ShiftsEnds"])

    # Taka saman hvað hver starfsmaður vinnur mikið
    total_work_hours = []

    for emp_id in selected_employee_ids:
        hours_per_employee[emp_id] += shift_hours
        employee_days[emp_id].add(event_date)
        total_work_hours.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            "ShiftHours": shift_hours,
            "TotalHours": hours_per_employee[emp_id]
        })

    return total_work_hours, next_index