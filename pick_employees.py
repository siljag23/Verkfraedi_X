from datetime import datetime, timedelta, time
from shift_length import shift_length
import math


def pick_employees(dict_events, dict_employees, hours_per_employee, employee_days, event_id: int, next_index: int, 
                   daily_hours_per_employee, max_daily_hours, assigned_shifts, min_rest_hours):
    
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

    shift_begins = datetime.combine(event_date, event["ShiftBegins"])
    shift_ends = datetime.combine(event_date, event["ShiftsEnds"])

    # Ef vakt nær yfir miðnætti 
    if shift_ends < shift_begins:
        shift_ends += timedelta(days=1)

    total_shift_hours = shift_length(event["ShiftBegins"], event["ShiftsEnds"])

    day_1 = shift_begins.date()
    day_2 = shift_ends.date()
    hours_day_1 = total_shift_hours
    hours_day_2 = 0

    # Ef vakt nær yfir miðnætti telst vaktin sem 2 dagar
    if day_1 != day_2 and shift_ends.time() != time(0, 0):
        hours_day_1 = shift_length(event["ShiftBegins"], time(0, 0))
        hours_day_2 = shift_length(time(0, 0), event["ShiftsEnds"])

    # Starfsmaður má ekki fá tvær vaktir sama dag
    blocked_days = {shift_begins.date()}

    event_score = float(event.get("EventRanking", 0))
    rest_delta = timedelta(hours=min_rest_hours)

    def to_int(x, default=0):
        """Hreinsar gögn úr excel (hugsað fyrir skillset fyrir viðburði)"""
        if x is None:
            return default
        if isinstance(x, float) and math.isnan(x):
            return default
        try:
            return int(x)
        except:
            return default

    # Fjöldi sem þarf með skillset 1 og 2
    req_skillset_1 = to_int(event.get("Skillset1"))
    req_skillset_2 = to_int(event.get("Skillset2"))

    # Villa ef fjöldi sem þarf með skillset1 + skillset2 er hærri en fjöldi starfsmanna sem þarf á viðburðinn
    if req_skillset_1 + req_skillset_2 > req_employees:
        raise ValueError(
            f"Skillset1 + Skillset2 ({req_skillset_1 + req_skillset_2}) > Employees ({req_employees}) fyrir Event {event_id}"
        )


    def respects_min_rest(emp_id: int) -> bool:
        """Athugum hvort starfsmenn uppfylli hvíldartímann"""
        for old_begins, old_ends in assigned_shifts.get(emp_id, []):
            ok = (shift_begins >= old_ends + rest_delta) or (old_begins >= shift_ends + rest_delta)
            if not ok:
                return False
        return True


    def is_eligible(emp_id: int) -> bool:
        """Athugum hvort starfsmaður hentar fyrir viðburðinn
           Tökum tillit til þess hvort starfsmaður sé núþegar að vinna þennan dag,
           hvort starfsmaðurinn fari yfir leyfilegan vinnutíma þennan dag og
           hvort starfsmaðurinn uppfylli hvíldartímann"""
        if employee_days[emp_id] & blocked_days:
            return False

        if daily_hours_per_employee[(emp_id, day_1)] + hours_day_1 > max_daily_hours:
            return False

        if hours_day_2 > 0:
            if daily_hours_per_employee[(emp_id, day_2)] + hours_day_2 > max_daily_hours:
                return False

        if not respects_min_rest(emp_id):
            return False

        return True


    def sort_key(emp_id: int):
        """Sorterum starfsmenn eftir score, hours ef score er jafnt, síðan eftir ID ef hitt er jafnt"""
        return (
            dict_employees[emp_id].get("Score", 0),
            hours_per_employee.get(emp_id, 0),
            emp_id
        )

    def emp_skill(emp_id: int) -> int:
        """Passar að skillset starfsmanna sé int"""
        return to_int(dict_employees[emp_id].get("Skillset", 0), 0)

    
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

    # --- Selection: skillset1 -> skillset2 -> rest ---
    selected_set = set()
    selected_employee_ids = []

    # 1) Skillset 1
    skill1_candidates = [eid for eid in dict_employees.keys() if emp_skill(eid) == 1]
    picked1 = pick_from(skill1_candidates, req_skillset_1, selected_set)
    selected_set.update(picked1)
    selected_employee_ids.extend(picked1)

    if len(picked1) < req_skillset_1:
        raise ValueError(
            f"Vantar {req_skillset_1 - len(picked1)} starfsmenn með Skillset 1 fyrir Event {event_id}"
        )

    # 2) Skillset 2
    skill2_candidates = [eid for eid in dict_employees.keys() if emp_skill(eid) == 2]
    picked2 = pick_from(skill2_candidates, req_skillset_2, selected_set)
    selected_set.update(picked2)
    selected_employee_ids.extend(picked2)

    if len(picked2) < req_skillset_2:
        raise ValueError(
            f"Vantar {req_skillset_2 - len(picked2)} starfsmenn með Skillset 2 fyrir Event {event_id}"
        )

    # 3) Rest
    remaining = req_employees - len(selected_employee_ids)
    if remaining > 0:
        all_candidates = list(dict_employees.keys())
        picked_rest = pick_from(all_candidates, remaining, selected_set)
        selected_set.update(picked_rest)
        selected_employee_ids.extend(picked_rest)

    if len(selected_employee_ids) < req_employees:
        raise ValueError(
            f"Ekki nægur fjöldi af starfsmönnum laus. Þarf {req_employees} en það eru {len(selected_employee_ids)}. "
            f"Þeir sem komast: {selected_employee_ids}"
        )

    # --- Apply updates ---
    shift_hours = shift_length(event["ShiftBegins"], event["ShiftsEnds"])
    total_work_hours = []

    for emp_id in selected_employee_ids:
        hours_per_employee[emp_id] += shift_hours
        employee_days[emp_id].update(blocked_days)

        daily_hours_per_employee[(emp_id, day_1)] += hours_day_1
        if hours_day_2 > 0:
            daily_hours_per_employee[(emp_id, day_2)] += hours_day_2

        assigned_shifts[emp_id].append((shift_begins, shift_ends))

        dict_employees[emp_id]["Score"] = dict_employees[emp_id].get("Score", 0) + event_score

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

    return total_work_hours, next_index