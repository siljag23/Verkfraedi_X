from datetime import datetime, timedelta, time
from shift_length import shift_length


def pick_employees(dict_events, dict_employees, hours_per_employee, employee_days, event_id: int, next_index: int, daily_hours_per_employee, max_daily_hours, time_last_shift_ended, min_rest_hours):

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

    total_shift_hours = shift_length(event["ShiftBegins"], event["ShiftsEnds"])

    # Teljum klst. í hverri vakt og skiptum niður á dag 1 og 2 (ef vaktin skyldi fara yfir miðnætti)
    day_1 = shift_begins.date()
    day_2 = shift_ends.date()
    hours_day_1 = total_shift_hours
    hours_day_2 = 0

    # Ef vakt fer yfir miðnætti þá fara klst. eftir miðnætti á dag 2
    if day_1 != day_2 and shift_ends.time() != time(0, 0):
        hours_day_1 = shift_length(event["ShiftBegins"], time(0, 0))
        hours_day_2 = shift_length(time(0, 0), event["ShiftsEnds"])

    # Ef þú ert með vakt á ákveðnum degi getur þú ekki fengið aðra vakt á þeim degi
    blocked_days = {shift_begins.date()}

    """
    # Raða starfsmönnum í stafrófsröð, ef starfsmenn heita það saman þá raða eftir ID
    sorted_employee_ids = [
        emp_id
        for emp_id, info in sorted(
            dict_employees.items(),
            key=lambda item: (item[1].get("EmployeeName", ""), item[0])
        )
    ]
    """

    # Sæki stig hvers viðburðar
    event_score = float(event.get("EventRanking", 0))

    # Raða starfsmönnum eftir stigafjölda, starfsmenn með lægstu stigin koma efst
    sorted_employees = sorted(
        dict_employees.keys(),
        key = lambda emp_id: (
            dict_employees[emp_id].get("Score", 0),
            dict_employees[emp_id].get("EmployeeName", ""),
            emp_id
        )
    )

    print("Event", event_id, "event_score", event_score)
    print("Top 10 (ID,Score):", [(eid, dict_employees[eid].get("Score", 0)) for eid in sorted_employees[:]])

    """
    print(sorted_employees)
    """

    # Velja starfsmenn með lægstu stig og brjóta engar skorður
    selected_employee_ids = []

    # Skoðum hvort starfsmaður getur unnið þennan dag
    for emp_id in sorted_employees:
        if len(selected_employee_ids) >= req_employees:
            break

        if employee_days[emp_id] & blocked_days:
            continue
    
        # Athugum hvort starfsmaður færi yfir hámarks klst. á degi 1
        if daily_hours_per_employee[(emp_id, day_1)] + hours_day_1 > max_daily_hours:
            continue

        # Athugum hvort starfsmaður færi yfir hámarks klst. á degi 2 (á við ef vaktin fer yfir miðnætti)
        if hours_day_2 > 0:
            if daily_hours_per_employee[(emp_id, day_2)] + hours_day_2 > max_daily_hours:
                continue


        # Athugum hvort starfsmaður fái a.m.k. lágmarks hvíld
        previous_shift_end = time_last_shift_ended.get(emp_id)
        if previous_shift_end is not None:
            if shift_begins - previous_shift_end < timedelta(hours=min_rest_hours):
                continue

        selected_employee_ids.append(emp_id)

    # Athugum hvort það sé nægur fjöldi starfsmanna laus fyrir vakt
    if len(selected_employee_ids) < req_employees:
        raise ValueError(
            f"Ekki nægur fjöldi af starfsmönnum laus þennan dag. "
            f"Þarf {req_employees} starfsmenn en aðeins {len(selected_employee_ids)} eru lausir. "
            f"Lausir: {selected_employee_ids}"
        )

    # Sækjum lengd hverrar vaktar í klst.
    shift_hours = shift_length(event["ShiftBegins"], event["ShiftsEnds"])

    # Taka saman hvað hver starfsmaður vinnur mikið
    total_work_hours = []

    for emp_id in selected_employee_ids:
        # Uppfæra heildarklst
        hours_per_employee[emp_id] += shift_hours

        # Banna aðra vakt sama dag (dagur sem vakt byrjar)
        employee_days[emp_id].update(blocked_days)

        # Uppfæra daglega klst á day_1 og day_2
        daily_hours_per_employee[(emp_id, day_1)] += hours_day_1
        if hours_day_2 > 0:
            daily_hours_per_employee[(emp_id, day_2)] += hours_day_2

        # Uppfæra hvenær síðasta vakt endaði (fyrir min_rest_hours regluna)
        time_last_shift_ended[emp_id] = shift_ends

        # Uppfæra Score starfsmanns (bætist við stig viðburðarins)
        dict_employees[emp_id]["Score"] = dict_employees[emp_id].get("Score", 0) + event_score

        total_work_hours.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            "ShiftHours": shift_hours,
            "TotalHours": hours_per_employee[emp_id],
            "AddedScore": event_score,
            "NewScore": dict_employees[emp_id]["Score"],
        })


    return total_work_hours, next_index




    
 
    """
    # Velja starfsmenn með round-robin eftir starfrófsröð
    # Sleppa þeim sem eru búnir að vinna sama dag
    selected_employee_ids = []
    total_employees = len(sorted_employee_ids)
    i = next_index
    employees_checked = 0
    """

    """
    # Hér er valið eftir stafsrófsröð
    while len(selected_employee_ids) < req_employees and employees_checked < total_employees:
        emp_id = sorted_employee_ids[i % total_employees]
        i += 1
        employees_checked += 1

        # Skoða hvort dagsetning viburðar sé laus hjá starfsmanni
        # Hoppa yfir starfsmann ef hann er ekki laus (continue)
        if employee_days[emp_id] & blocked_days:
            continue

        # Athugum hvort starfsmaður færi yfir hámarks klst. á degi 1
        # Ef hann fer yfir hámarkið þá hoppum við yfir starfsmanninn
        if daily_hours_per_employee[(emp_id, day_1)] + hours_day_1 > max_daily_hours:
            continue
        
        # Athugum hvort starfsmaður færi yfir hámarks klst. á degi 2 (á við ef vaktin fer yfir miðnætti)
        # Ef hann fer yfir hámarkið þá hoppum við yfir starsfmanninn
        if hours_day_2 > 0:
            if daily_hours_per_employee[(emp_id, day_2)] + hours_day_2 > max_daily_hours:
                continue
        
        # Athugum hvort starfsmaður fái a.m.k. lágmarks hvíld
        # Hoppum yfir starfsmanninn ef hann fengi ekki lágmarks hvíld
        previous_shift_end = time_last_shift_ended.get(emp_id)
        if previous_shift_end is not None:
            if shift_begins - previous_shift_end < timedelta(hours=min_rest_hours):
                continue

        selected_employee_ids.append(emp_id)    

    # Athugum hvort það sé nægur fjöldi starfsmanna laus fyrir vakt
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
        employee_days[emp_id].update(blocked_days)
        total_work_hours.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            "ShiftHours": shift_hours,
            "TotalHours": hours_per_employee[emp_id]
        })

    

    return total_work_hours, next_index
    """