from datetime import datetime, timedelta, time
from shift_length import shift_length
import math


def pick_employees(dict_events, dict_employees, hours_per_employee, employee_days_off, event_id: int, next_index: int, 
                   daily_hours_per_employee, max_daily_hours, assigned_shifts, min_rest_hours, employee_worked_days):
    
    event = dict_events[event_id]
    req_employees = int(event["Employees"])

    def parse_event_date(ev):
        raw = ev["Date"]
        if isinstance(raw, str):
            return datetime.strptime(raw.strip(), "%d.%m.%Y").date()
        elif hasattr(raw, "date"):
            return raw.date()
        return raw

    all_event_dates = [parse_event_date(ev) for ev in dict_events.values()]
    period_end = max(all_event_dates)

    period_days = (period_end - period_start).days + 1
    period_weeks = period_days / 7
    if period_weeks <= 0:
        period_weeks = 1
        
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
    
    def respects_max_6_days_in_7(emp_id: int) -> bool:
        proposed_days = set(employee_worked_days[emp_id]) | blocked_days

        if not proposed_days:
            return True

        sorted_days = sorted(proposed_days)

        for start_day in sorted_days:
            window_end = start_day + timedelta(days=6)
            days_in_window = sum(1 for d in proposed_days if start_day <= d <= window_end)

            if days_in_window > 6:
                print(
                    f"EMP {emp_id} HAFNAÐ -> meira en 6 vinnudagar á 7 daga tímabili. "
                    f"Gluggi: {start_day} til {window_end}, "
                    f"vinnudagar í glugga: {days_in_window}"
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

        if not respects_max_6_days_in_7(emp_id):
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
        
        projected_total_hours = hours_per_employee.get(emp_id, 0) + total_shift_hours
        avg_weekly_hours = projected_total_hours / period_weeks

        if avg_weekly_hours > 48:
            print(
                f"EMP {emp_id} HAFNAÐ -> fer yfir 48 klst/viku að meðaltali. "
                f"Heild eftir vakt: {projected_total_hours:.2f}, "
                f"vikur á tímabili: {period_weeks:.2f}, "
                f"meðaltal: {avg_weekly_hours:.2f}"
            )
            return False

        if not respects_min_rest(emp_id):
            return False

        # Ef starfsmaður brýtur enga af skorðunum fyrir ofan fær hann vaktina
        """print(f"EMP {emp_id} SAMÞYKKTUR fyrir Event {event_id} á {event_date}")"""
        return True

    def sort_key(emp_id: int):
        raw_category = event.get("Category", "")
        category = "" if raw_category is None else str(raw_category).strip()

        if category.lower() == "nan":
            category = ""

        prev_category_count = 0
        if category:
            prev_category_count = dict_employees[emp_id].get(
                "prev_shifts_per_category", {}
            ).get(category, 0)

        return (
            to_number(dict_employees[emp_id].get("Score", 0), 0), 
            prev_category_count,
            to_number(hours_per_employee.get(emp_id, 0), 0),
            emp_id
        )

    def emp_skill(emp_id: int) -> int:
        return to_int(dict_employees[emp_id].get("Skillset", 0), 0)

    def is_valid_team(team_ids: list[int]) -> bool:
        if not team_ids:
            return True

        skills = [emp_skill(emp_id) for emp_id in team_ids]

        # Ef einhver skillset 3 er á vakt, þá verður að vera
        # a.m.k. einn annar starfsmaður sem er ekki með skillset 3
        if 3 in skills and all(skill == 3 for skill in skills):
            return False

        return True

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

    def pick_remaining_candidates(
        candidates: list[int], n: int, selected_set: set[int]
    ) -> list[int]:
        picked = []

        def remaining_sort_key(emp_id: int):
            current_team = selected_employee_ids + picked
            current_skills = [emp_skill(eid) for eid in current_team]

            # Ef það er nú þegar skillset 3 í hópnum,
            # þá viljum við forgangsraða starfsmönnum sem eru EKKI skillset 3
            needs_non3 = 3 in current_skills and all(skill == 3 for skill in current_skills)

            prefer_non3 = 0
            if needs_non3:
                prefer_non3 = 0 if emp_skill(emp_id) != 3 else 1

            return (
                prefer_non3,
                *sort_key(emp_id)
            )

        for emp_id in sorted(candidates, key=remaining_sort_key):
            if len(picked) >= n:
                break
            if emp_id in selected_set:
                continue
            if not is_eligible(emp_id):
                continue

            trial_team = selected_employee_ids + picked + [emp_id]
            slots_left_after = n - (len(picked) + 1)

            # Ef þetta er síðasta sætið, þá verður lokahópurinn að vera löglegur
            if slots_left_after == 0 and not is_valid_team(trial_team):
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
        picked_rest = pick_remaining_candidates(all_candidates, remaining, selected_set)
        selected_set.update(picked_rest)
        selected_employee_ids.extend(picked_rest)

    if len(selected_employee_ids) < req_employees:
        raise ValueError(
            f"Ekki nægur fjöldi af starfsmönnum laus. Þarf {req_employees} en það eru {len(selected_employee_ids)} lausir. "
            f"Þeir sem komast eru með ID {selected_employee_ids}"
        )
    
    if not is_valid_team(selected_employee_ids):
        replacement_found = False

        for emp_id in sorted(dict_employees.keys(), key=sort_key):
            if emp_id in selected_set:
                continue
            if emp_skill(emp_id) == 3:
                continue
            if not is_eligible(emp_id):
                continue

            # Prófum að skipta út einum skillset 3
            for i, chosen_id in enumerate(selected_employee_ids):
                if emp_skill(chosen_id) == 3:
                    trial_team = selected_employee_ids.copy()
                    trial_team[i] = emp_id

                    if is_valid_team(trial_team):
                        selected_set.remove(chosen_id)
                        selected_set.add(emp_id)
                        selected_employee_ids[i] = emp_id
                        replacement_found = True
                        break

            if replacement_found:
                break

        if not is_valid_team(selected_employee_ids):
            raise ValueError(
                f"Skillset 3 starfsmenn mega ekki vera einir eða bara saman á vakt fyrir Event {event_id}. "
                f"Valdir: {selected_employee_ids}"
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

    raw_hall = event.get("Hall", "")
    hall = "" if raw_hall is None else str(raw_hall).strip()
    if hall.lower() == "nan":
        hall = ""

    raw_category = event.get("Category", "")
    category = "" if raw_category is None else str(raw_category).strip()
    if category.lower() == "nan":
        category = ""

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

        dict_employees[emp_id]["Number_of_shifts"] = (
            to_int(dict_employees[emp_id].get("Number_of_shifts"), 0) + 1
        )

        # Teljum hversu margar vaktir starfsmaður fær um helgi
        if event_date.weekday() in [4, 5, 6]:
            dict_employees[emp_id]["Shifts_on_weekends"] = (
                to_int(dict_employees[emp_id].get("Shifts_on_weekends"), 0) + 1
            )

            
        # Teljum hversu margar vaktir hver starfsmaður fær í hverjum sal
        if hall:
            if "Shifts_per_hall" not in dict_employees[emp_id] or not isinstance(dict_employees[emp_id]["Shifts_per_hall"], dict):
                dict_employees[emp_id]["Shifts_per_hall"] = {}

            current_hall_count = to_int(
                dict_employees[emp_id]["Shifts_per_hall"].get(hall, 0), 0
            )
            dict_employees[emp_id]["Shifts_per_hall"][hall] = current_hall_count + 1

        if category:
            if (
                "current_shifts_per_category" not in dict_employees[emp_id]
                or not isinstance(dict_employees[emp_id]["current_shifts_per_category"], dict)
            ):
                dict_employees[emp_id]["current_shifts_per_category"] = {}

            current_cat_count = to_int(
                dict_employees[emp_id]["current_shifts_per_category"].get(category, 0), 0
            )
            dict_employees[emp_id]["current_shifts_per_category"][category] = current_cat_count + 1

        total_work_hours.append({
            "EventID": event_id,
            "EmployeeID": emp_id,
            "EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            "EmployeeSkillset": dict_employees[emp_id].get("Skillset"),
            "ShiftHours": shift_hours,
            "TotalHours": hours_per_employee[emp_id],
            "AddedScore": event_score,
            "NewScore": dict_employees[emp_id]["Score"],
            "NumberOfShifts": dict_employees[emp_id]["Number_of_shifts"],
            "ShiftsOnWeekends": dict_employees[emp_id]["Shifts_on_weekends"],
            "ShiftsPerHall": dict_employees[emp_id]["Shifts_per_hall"].get(hall, 0) if hall else 0,
            "CurrentShiftsPerCategory": dict_employees[emp_id]["current_shifts_per_category"]. get(category, 0) if category else 0
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