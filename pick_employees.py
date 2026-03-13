from datetime import datetime, timedelta, time
from shift_length import shift_length
import math


def pick_employees(dict_events, dict_employees, hours_per_employee, employee_days_off, event_id: int, next_index: int, 
                   daily_hours_per_employee, max_daily_hours, assigned_shifts, min_rest_hours, employee_worked_days):
    
    event = dict_events[event_id]
    req_employees = int(event["Employees"])

    # Athugum hvort date sé formattað sem dagsetning, ef ekki er það lagað
    raw_date = event["Date"]
    if isinstance(raw_date, str):
        event_date = datetime.strptime(raw_date.strip(), "%d.%m.%Y").date()
    elif hasattr(raw_date, "date"):
        event_date = raw_date.date()
    else:
        event_date = raw_date

    # Breytum tíma úr Excel/pandas í datetime.time ef hann kemur sem timedelta
    def ensure_time(x):
        if isinstance(x, time):
            return x
        if isinstance(x, timedelta):
            total_seconds = int(x.total_seconds())
            hours = (total_seconds // 3600) % 24
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return time(hours, minutes, seconds)
        if hasattr(x, "time"):
            return x.time()
        if isinstance(x, str):
            x = x.strip()
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(x, fmt).time()
                except ValueError:
                    pass
        raise ValueError(f"Óþekkt tímaformat: {x} ({type(x)})")

    shift_begins_time = ensure_time(event["ShiftBegins"])
    shift_ends_time = ensure_time(event["ShiftEnds"])

    shift_begins = datetime.combine(event_date, shift_begins_time)
    shift_ends = datetime.combine(event_date, shift_ends_time)

    # Ef vakt nær yfir miðnætti
    if shift_ends < shift_begins:
        shift_ends += timedelta(days=1)

    total_shift_hours = shift_length(shift_begins_time, shift_ends_time)

    day_1 = shift_begins.date()
    day_2 = shift_ends.date()
    hours_day_1 = total_shift_hours
    hours_day_2 = 0

    # Ef vakt nær yfir miðnætti telst vaktin sem 2 dagar
    if day_1 != day_2 and shift_ends.time() != time(0, 0):
        hours_day_1 = shift_length(shift_begins_time, time(0, 0))
        hours_day_2 = shift_length(time(0, 0), shift_ends_time)

    # Starfsmaður má ekki fá tvær vaktir sama dag
    blocked_days = {day_1}
    if hours_day_2 > 0:
        blocked_days.add(day_2)

    event_score = float(event.get("EventRanking", 0))
    rest_delta = timedelta(hours=min_rest_hours)

    def to_int(x, default=0):
        if x is None:
            return default
        if isinstance(x, float) and math.isnan(x):
            return default
        try:
            return int(x)
        except:
            return default

    def to_number(x, default=0):
        if x is None:
            return default
        if isinstance(x, float) and math.isnan(x):
            return default
        try:
            return float(x)
        except:
            return default

    req_skillset_1 = to_int(event.get("Skillset1"))
    req_skillset_2 = to_int(event.get("Skillset2"))

    if req_skillset_1 + req_skillset_2 > req_employees:
        raise ValueError(
            f"Skillset1 + Skillset2 ({req_skillset_1 + req_skillset_2}) > Employees ({req_employees}) fyrir Event {event_id}"
        )

    def respects_min_rest(emp_id: int) -> bool:
        for old_begins, old_ends in assigned_shifts.get(emp_id, []):
            ok = (shift_begins >= old_ends + rest_delta) or (old_begins >= shift_ends + rest_delta)
            if not ok:
                print(
                    f"EMP {emp_id} HAFNAÐ -> brýtur hvíldartíma. "
                    f"Gamla vakt: {old_begins} til {old_ends}, "
                    f"ný vakt: {shift_begins} til {shift_ends}, "
                    f"minnst {min_rest_hours} klst hvíld"
                )
                return False
        return True

    def is_eligible(emp_id: int) -> bool:
        # Athugum hvort starfsmaður sé í fríi þennan dag
        if event_date in employee_days_off[emp_id]:
            print(
                f"EMP {emp_id} HAFNAÐ -> í fríi á {event_date}. "
                f"employee_days_off[{emp_id}] = {sorted(employee_days_off[emp_id])}"
            )
            return False
        
        # Athugum hvort starsfmaður sé kominn með vakt þennan dag
        if employee_worked_days[emp_id] & blocked_days:
            print(
                f"EMP {emp_id} HAFNAÐ -> þegar bókaður {event_date}. "
                f"blocked_days = {blocked_days}, "
                f"employee_worked_days[{emp_id}] = {sorted(employee_worked_days[emp_id])}"
            )
            return False

        # Athugum hvort hvíldartíminn yrði brotinn ef starsfmaður fær vaktina
        if daily_hours_per_employee[(emp_id, day_1)] + hours_day_1 > max_daily_hours:
            print(
                f"EMP {emp_id} HAFNAÐ -> fer yfir max dagklst á {day_1}. "
                f"Núna: {daily_hours_per_employee[(emp_id, day_1)]}, "
                f"bætast við: {hours_day_1}, max: {max_daily_hours}"
            )
            return False

        if hours_day_2 > 0:
            if daily_hours_per_employee[(emp_id, day_2)] + hours_day_2 > max_daily_hours:
                print(
                    f"EMP {emp_id} HAFNAÐ -> fer yfir max dagklst á {day_2}. "
                    f"Núna: {daily_hours_per_employee[(emp_id, day_2)]}, "
                    f"bætast við: {hours_day_2}, max: {max_daily_hours}"
                )
                return False

        if not respects_min_rest(emp_id):
            return False

        # Ef starfsmaður brýtur enga af skorðunum fyrir ofan fær hann vaktina
        """print(f"EMP {emp_id} SAMÞYKKTUR fyrir Event {event_id} á {event_date}")"""
        return True

    def sort_key(emp_id: int):
        return (
            to_number(dict_employees[emp_id].get("Score", 0), 0),
            to_number(hours_per_employee.get(emp_id, 0), 0),
            emp_id
        )

    def emp_skill(emp_id: int) -> int:
        return to_int(dict_employees[emp_id].get("Skillset", 0), 0)

    for emp_id in dict_employees:
        dict_employees[emp_id]["Score"] = to_number(
            dict_employees[emp_id].get("Score", 0), 0
        )

    def pick_from(candidates: list[int], n: int, selected_set: set[int]) -> list[int]:
        picked = []
        for emp_id in sorted(candidates, key=sort_key):
            if len(picked) >= n:
                break
            if emp_id in selected_set:
                continue
            if not is_eligible(emp_id):
                continue
            picked.append(emp_id)
        return picked

    selected_set = set()
    selected_employee_ids = []

    skill1_candidates = [eid for eid in dict_employees.keys() if emp_skill(eid) == 1]
    picked1 = pick_from(skill1_candidates, req_skillset_1, selected_set)
    selected_set.update(picked1)
    selected_employee_ids.extend(picked1)

    if len(picked1) < req_skillset_1:
        raise ValueError(
            f"Vantar {req_skillset_1 - len(picked1)} starfsmenn með Skillset 1 fyrir Event {event_id}"
        )

    skill2_candidates = [eid for eid in dict_employees.keys() if emp_skill(eid) == 2]
    picked2 = pick_from(skill2_candidates, req_skillset_2, selected_set)
    selected_set.update(picked2)
    selected_employee_ids.extend(picked2)

    if len(picked2) < req_skillset_2:
        raise ValueError(
            f"Vantar {req_skillset_2 - len(picked2)} starfsmenn með Skillset 2 fyrir Event {event_id}"
        )

    remaining = req_employees - len(selected_employee_ids)
    if remaining > 0:
        all_candidates = list(dict_employees.keys())
        picked_rest = pick_from(all_candidates, remaining, selected_set)
        selected_set.update(picked_rest)
        selected_employee_ids.extend(picked_rest)

    if len(selected_employee_ids) < req_employees:
        raise ValueError(
            f"Ekki nægur fjöldi af starfsmönnum laus. Þarf {req_employees} en það eru {len(selected_employee_ids)} lausir. "
            f"Þeir sem komast eru með ID {selected_employee_ids}"
        )

    # DEBUG 2 # öryggistékk: enginn valinn starfsmaður má vera í fríi eða brjóta hvíldartíma
    for emp_id in selected_employee_ids:
        if event_date in employee_days_off[emp_id]:
            raise ValueError(
                f"VILLA: starfsmaður {emp_id} var valinn fyrir Event {event_id} "
                f"þótt hann sé í fríi á {event_date}. "
                f"employee_days_off[{emp_id}] = {sorted(employee_days_off[emp_id])}"
            )

        if employee_worked_days[emp_id] & blocked_days:
            raise ValueError(
                f"VILLA: starfsmaður {emp_id} var valinn fyrir Event {event_id} "
                f"þótt hann sé nú þegar bókaður á dag. "
                f"blocked_days = {blocked_days}, "
                f"employee_worked_days[{emp_id}] = {sorted(employee_worked_days[emp_id])}"
            )

        if not respects_min_rest(emp_id):
            raise ValueError(
                f"VILLA: starfsmaður {emp_id} var valinn fyrir Event {event_id} "
                f"þótt hann brjóti hvíldartíma. "
                f"assigned_shifts[{emp_id}] = {assigned_shifts.get(emp_id, [])}"
            )

    shift_hours = shift_length(shift_begins_time, shift_ends_time)
    total_work_hours = []

    for emp_id in selected_employee_ids:
        hours_per_employee[emp_id] += shift_hours
        employee_worked_days[emp_id].update(blocked_days)

        daily_hours_per_employee[(emp_id, day_1)] += hours_day_1
        if hours_day_2 > 0:
            daily_hours_per_employee[(emp_id, day_2)] += hours_day_2

        assigned_shifts[emp_id].append((shift_begins, shift_ends))

        dict_employees[emp_id]["Score"] = to_number(
            dict_employees[emp_id].get("Score", 0), 0
        ) + event_score

         # Teljum vakt sem helgarvakt ef hún byrjar á föstudegi, laugardegi eða sunnudegi
        if event_date.weekday() in [4, 5, 6]:
            dict_employees[emp_id]["Shifts_on_weekends"] = (
                to_int(dict_employees[emp_id].get("Shifts_on_weekends"), 0) + 1
            )

        total_work_hours.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            "EmployeeSkillset": dict_employees[emp_id].get("Skillset"),
            "ShiftHours": shift_hours,
            "TotalHours": hours_per_employee[emp_id],
            "AddedScore": event_score,
            "NewScore": dict_employees[emp_id]["Score"],
        })

    # Tékk á forgangsröðun fyrir næsta event
    """
    print(f"\nStaða eftir Event {event_id}")

    print("---- Fyrstu 5 ----")
    for emp_id in sorted_ids[:5]:
        print(
            f"ID={emp_id}, "
            f"Score={dict_employees[emp_id].get('Score', 0)}, "
            f"Hours={hours_per_employee.get(emp_id, 0)}"
        )

    print("---- Síðustu 5 ----")
    for emp_id in sorted_ids[-5:]:
        print(
            f"ID={emp_id}, "
            f"Score={dict_employees[emp_id].get('Score', 0)}, "
            f"Hours={hours_per_employee.get(emp_id, 0)}"
        )
    """

    return total_work_hours, next_index