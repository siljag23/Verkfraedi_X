from datetime import datetime, timedelta, time
from shift_length import shift_length


def assign_all_events(dict_events, dict_employees, hours_per_employee, employee_days_off, daily_hours_per_employee, max_daily_hours, max_weekly_hours, 
                      assigned_shifts, min_rest_hours, employee_worked_days, score_rules, skillset_scores, event_requests, base_min_shifts):
    """
    Aðalfall:
    - velur starfsmann fyrst út frá forgangi
    - finnur bestu lausu vakt / hlutverk fyrir hann
    - úthlutar honum því
    - endurtekur þar til allar vaktir eru fullmannaðar eða ekkert gengur lengur

    Skilar:
    - all_work_results: listi með öllum úthlutunum
    - event_state: staða allra viðburða eftir úthlutun
    """

    def lookup_score(rule_dict: dict, key: int, default=0):
        """
        Sækir score fyrir tiltekinn lykil úr reglutöflu.

        Ef lykillinn finnst ekki:
        - og er stærri en hæsti skilgreindi lykillinn, þá er notað score fyrir hæsta lykil
        - annars default
        """
        if not rule_dict:
            return default

        if key in rule_dict:
            return rule_dict[key]

        max_key = max(rule_dict.keys())
        if key > max_key:
            return rule_dict[max_key]

        return default

    # Reiknum tímabil fyrir 48 klst/viku meðaltalsreglu
    all_event_dates = [ev["Date"] for ev in dict_events.values()]
    period_start = min(all_event_dates)
    period_end = max(all_event_dates)

    period_days = (period_end - period_start).days + 1
    period_weeks = period_days / 7
    if period_weeks <= 0:
        period_weeks = 1

    # Reikna lágmarksvaktir m.v. frí - starfsmaður í engu fríi á að fá a.m.k. 3 vaktir
    for emp_id in dict_employees:
        ratio = dict_employees[emp_id].get("availability_ratio", 1.0)
        dict_employees[emp_id]["min_shifts"] = round(base_min_shifts * ratio)

    def get_event_datetime_info(event_id: int):
        """Sækir allar grunnupplýsingar um dagsetningu, tíma og skiptingu vaktar á daga"""
        event = dict_events[event_id]

        raw_date = event["Date"]
        if isinstance(raw_date, str):
            event_date = datetime.strptime(raw_date.strip(), "%d.%m.%Y").date()
        elif hasattr(raw_date, "date"):
            event_date = raw_date.date()
        else:
            event_date = raw_date

        shift_begins_time = event["ShiftBegins"]
        shift_ends_time = event["ShiftEnds"]

        shift_begins_date = datetime.combine(event_date, shift_begins_time)
        shift_ends_date = datetime.combine(event_date, shift_ends_time)

        if shift_ends_date < shift_begins_date:
            shift_ends_date += timedelta(days=1)

        total_shift_hours = shift_length(shift_begins_time, shift_ends_time)

        day_1 = shift_begins_date.date()
        day_2 = shift_ends_date.date()
        hours_day_1 = total_shift_hours
        hours_day_2 = 0

        if day_1 != day_2 and shift_ends_date.time() != time(0, 0):
            hours_day_1 = shift_length(shift_begins_time, time(0, 0))
            hours_day_2 = shift_length(time(0, 0), shift_ends_time)

        blocked_days = {day_1}
        if hours_day_2 > 0:
            blocked_days.add(day_2)

        return {
            "event_date": event_date,
            "shift_begins_time": shift_begins_time,
            "shift_ends_time": shift_ends_time,
            "shift_begins": shift_begins_date,
            "shift_ends": shift_ends_date,
            "total_shift_hours": total_shift_hours,
            "day_1": day_1,
            "day_2": day_2,
            "hours_day_1": hours_day_1,
            "hours_day_2": hours_day_2,
            "blocked_days": blocked_days,
        }

    def build_event_roles(event_id: int):
        """
        Býr til hlutverk fyrir event.
        Dæmi: Employees=3, Skillset1=1, Skillset2=1
        =>
        [{"role_id": 0, "required_skill": 1},
         {"role_id": 1, "required_skill": 2},
         {"role_id": 2, "required_skill": None}]
        """
        event = dict_events[event_id]
        
        req_employees = event["Employees"]
        req_skillset_1 = event["Skillset1"]
        req_skillset_2 = event["Skillset2"]

        roles = []
        role_id = 0

        if req_skillset_1 + req_skillset_2 > req_employees:
            raise ValueError(
                f"Skillset1 + Skillset2 ({req_skillset_1 + req_skillset_2}) > Employees ({req_employees}) fyrir Event {event_id}")

        for _ in range(req_skillset_1):
            roles.append({
                "role_id": role_id,
                "required_skill": 1,
                "filled_by": None})
            role_id += 1

        for _ in range(req_skillset_2):
            roles.append({
                "role_id": role_id,
                "required_skill": 2,
                "filled_by": None})
            role_id += 1

        remaining = req_employees - req_skillset_1 - req_skillset_2
        for _ in range(remaining):
            roles.append({
                "role_id": role_id,
                "required_skill": None,
                "filled_by": None})
            role_id += 1

        return roles

    def respects_min_rest(emp_id: int, shift_begins: datetime, shift_ends: datetime) -> bool:
        """Athugar hvort starfsmenn uppfylli lágmarks hvíldartíma milli vakta"""
        rest_delta = timedelta(hours=min_rest_hours)

        for prev_begins, prev_ends in assigned_shifts.get(emp_id, []):
            ok = (shift_begins >= prev_ends + rest_delta) or (prev_begins >= shift_ends + rest_delta)
            if not ok:
                return False
        return True

    def respects_max_6_days_in_7(emp_id: int, blocked_days: set) -> bool:
        """Athugar hvort starfsmenn vinni nokkuð meira en 6 daga á 7 daga tímabili"""
        proposed_days = set(employee_worked_days[emp_id]) | blocked_days

        if not proposed_days:
            return True

        sorted_days = sorted(proposed_days)

        for start_day in sorted_days:
            window_end = start_day + timedelta(days=6)
            days_in_window = sum(1 for d in proposed_days if start_day <= d <= window_end)

            if days_in_window > 6:
                return False

        return True

    def is_eligible_for_event(emp_id: int, event_id: int) -> bool:
        """Almenn gjaldgengni starfsmanns fyrir viðburð, óháð því hvaða hlutverk innan vaktar er valið"""
        datetime_info = get_event_datetime_info(event_id)

        event_date = datetime_info["event_date"]
        shift_begins = datetime_info["shift_begins"]
        shift_ends = datetime_info["shift_ends"]
        total_shift_hours = datetime_info["total_shift_hours"]
        day_1 = datetime_info["day_1"]
        day_2 = datetime_info["day_2"]
        hours_day_1 = datetime_info["hours_day_1"]
        hours_day_2 = datetime_info["hours_day_2"]
        blocked_days = datetime_info["blocked_days"]

        if event_date in employee_days_off[emp_id]:
            return False

        if employee_worked_days[emp_id] & blocked_days:
            return False

        if not respects_max_6_days_in_7(emp_id, blocked_days):
            return False

        if daily_hours_per_employee[(emp_id, day_1)] + hours_day_1 > max_daily_hours:
            return False

        if hours_day_2 > 0:
            if daily_hours_per_employee[(emp_id, day_2)] + hours_day_2 > max_daily_hours:
                return False

        projected_total_hours = hours_per_employee.get(emp_id, 0) + total_shift_hours
        avg_weekly_hours = projected_total_hours / period_weeks
        if avg_weekly_hours > max_weekly_hours:
            return False

        if not respects_min_rest(emp_id, shift_begins, shift_ends):
            return False

        return True

    def is_valid_final_team(employee_ids: list[int]) -> bool:
        """
        Lokatékk á hópnum þegar event er fullmannað.
        Núverandi regla: ef einhver skillset 3 er í hópnum, þá má hópurinn ekki eingöngu vera skillset 3
        """
        if not employee_ids:
            return True

        skills = [dict_employees[emp_id]["Skillset"] for emp_id in employee_ids]

        if 3 in skills and all(skill == 3 for skill in skills):
            return False

        return True

    def employee_priority(emp_id: int):
        """Raðar starfsmönnum í forgangsröð, sá sem er lengst frá því að uppfylla lágmarksfjölda vakta er efst"""
        number_of_current_shifts = dict_employees[emp_id]["Number_of_shifts"]
        min_shifts = dict_employees[emp_id].get("min_shifts", base_min_shifts)
        
        # Ef 0.0 = ekkert lokið, 1.0 = allt lokið
        if min_shifts > 0:
            completion_ratio = number_of_current_shifts / min_shifts
        else:
            completion_ratio = 1.0
        return (
            completion_ratio,                        
            dict_employees[emp_id]["Score"],
            number_of_current_shifts,
            hours_per_employee[emp_id],
            emp_id
        )

    def personal_role_score(emp_id: int, event_id: int, role: dict) -> float:
        """
        Persónuleg stig fyrir starfsmenn fyrir hvert hlutverk á hverjum event.
        HÆRRA score = betri kostur fyrir starfsmanninn.
        """
        event = dict_events[event_id]
        datetime_info = get_event_datetime_info(event_id)
        event_date = datetime_info["event_date"]
        total_shift_hours = datetime_info["total_shift_hours"]
        hall = event.get("Hall")
        event_score = event["EventRanking"]
        weekend_count = dict_employees[emp_id]["Shifts_on_weekends"]
        hall_count = dict_employees[emp_id].get("Shifts_per_hall", {}).get(hall, 0)
        emp_current_skill = dict_employees[emp_id]["Skillset"]
        required_skill = role.get("required_skill")

        # -----Stig sótt úr ScoreKeys úr excel input-----

        # Helgarvakt í núverandi tímabili
        weekend_adjustment = 0
        if event_date.weekday() in [4, 5, 6]:
            weekend_adjustment = lookup_score(
                score_rules.get("Weekend", {}), weekend_count, 0)

        # Helgarvaktir frá síðasta tímabili
        prev_weekend_count = dict_employees[emp_id]["prev_weekend_shifts"]
        weekend_last_period_adjustment = 0
        if event_date.weekday() in [4, 5, 6]:
            weekend_last_period_adjustment = lookup_score(
                score_rules.get("Weekend_last_period", {}), prev_weekend_count, 0)

        # Fjöldi vakta í sama sal
        hall_adjustment = 0
        if hall:
            hall_adjustment = lookup_score(
                score_rules.get("Hall", {}), hall_count, 0)

        # Fjöldi vakta í sömu viku og þessi vakt
        event_iso_year, event_iso_week, _ = event_date.isocalendar()
        week_key = f"{event_iso_year}-W{event_iso_week:02d}"

        shifts_this_week = dict_employees[emp_id].get("Shifts_per_week", {}).get(week_key, 0)

        shifts_this_week_adjustment = lookup_score(
            score_rules.get("Shifts_this_week", {}),
            shifts_this_week,
            0
        )

        # Fjöldi vakta af þessari lengd
        shift_length_key = int(round(total_shift_hours))

        current_count_same_length = dict_employees[emp_id].get("Shifts_per_length", {}).get(shift_length_key, 0)

        shift_length_adjustment = lookup_score(
            score_rules.get("Shifts_this_length", {}),
            current_count_same_length, 0)

        # Fjöldi vakta 6+ klst.
        shift_over_six_hours_adjustment = 0

        if total_shift_hours > 6:
            current_over_six_count = dict_employees[emp_id]["Shifts_over_six_hours"]

            shift_over_six_hours_adjustment = lookup_score(
                score_rules.get("Shift_over_six_hours", {}),
                current_over_six_count, 0)
            
        # Fjöldi vakta af sömu category
        category = event["EventCategory"]
        category_count = dict_employees[emp_id].get("current_shifts_per_category", {}).get(category, 0)

        category_adjustment = 0
        if category:
            category_adjustment = lookup_score(
                score_rules.get("Category", {}), category_count, 0)        

        # Skillset score úr SkillsetScores
        skill_adjustment = 0
        if required_skill is not None:
            skill_adjustment = skillset_scores.get(required_skill, {}).get(emp_current_skill, 0)

        req_adjustment = 0
        if (emp_id, event_id) in event_requests:
            req_adjustment = lookup_score(score_rules.get("Req_this_shift", {}), 1, 0)

        return (
            event_score
            + weekend_adjustment
            + weekend_last_period_adjustment
            + hall_adjustment
            + shifts_this_week_adjustment
            + shift_length_adjustment
            + shift_over_six_hours_adjustment
            + skill_adjustment
            + req_adjustment
            + category_adjustment
        )

    def choose_best_role_for_employee(emp_id: int, event_state: dict):
        """
        Finnur besta lausa hlutverkið fyrir starfsmann yfir alla eventa.
        Skilar t.d.
        {"event_id": 15,
         "role_id": 2,
         "score": 11.5}
        """
        best_option = None

        for event_id, state in event_state.items():
            for role in state["roles"]:
                if role["filled_by"] is not None:
                    continue
                if not is_eligible_for_event(emp_id, event_id):
                    continue
                current_team = [r["filled_by"] for r in event_state[event_id]["roles"] if r["filled_by"] is not None]
                if not is_valid_final_team(current_team + [emp_id]):
                    continue

                score = personal_role_score(emp_id, event_id, role)

                if best_option is None or score > best_option["score"]:
                    best_option = {
                        "event_id": event_id,
                        "role_id": role["role_id"],
                        "score": score}    
        
        return best_option

    def assign_employee_to_role(emp_id: int, event_id: int, role_id: int, event_state: dict):
        """Úthlutar starfsmanni á tiltekið hlutverk og uppfærir allar stöðubreytur"""
        event = dict_events[event_id]
        datetime_info = get_event_datetime_info(event_id)

        hall = event.get("Hall")
        category = event.get("EventCategory")

        event_date = datetime_info["event_date"]
        shift_begins = datetime_info["shift_begins"]
        shift_ends = datetime_info["shift_ends"]
        total_shift_hours = datetime_info["total_shift_hours"]
        day_1 = datetime_info["day_1"]
        day_2 = datetime_info["day_2"]
        hours_day_1 = datetime_info["hours_day_1"]
        hours_day_2 = datetime_info["hours_day_2"]
        blocked_days = datetime_info["blocked_days"]

        event_score = event["EventRanking"]

        # Merkjum role sem fyllt
        for role in event_state[event_id]["roles"]:
            if role["role_id"] == role_id:
                role["filled_by"] = emp_id
                break

        # Uppfærum stöður starfsmanns
        hours_per_employee[emp_id] += total_shift_hours
        employee_worked_days[emp_id].update(blocked_days)

        daily_hours_per_employee[(emp_id, day_1)] += hours_day_1
        if hours_day_2 > 0:
            daily_hours_per_employee[(emp_id, day_2)] += hours_day_2

        assigned_shifts[emp_id].append((shift_begins, shift_ends))

        dict_employees[emp_id]["Score"] += event_score

        
        dict_employees[emp_id]["Number_of_shifts"] += 1

        if event_date.weekday() in [4, 5, 6]:
            dict_employees[emp_id]["Shifts_on_weekends"] += 1

        if hall:
            dict_employees[emp_id]["Shifts_per_hall"][hall] = (
                dict_employees[emp_id]["Shifts_per_hall"].get(hall, 0) + 1)
        
        if category:
            dict_employees[emp_id]["current_shifts_per_category"][category] = (
                dict_employees[emp_id]["current_shifts_per_category"].get(category, 0) + 1)


        shift_length_key = int(round(total_shift_hours))
        dict_employees[emp_id]["Shifts_per_length"][shift_length_key] = (
            dict_employees[emp_id]["Shifts_per_length"].get(shift_length_key, 0) + 1)

        if total_shift_hours > 6:
            dict_employees[emp_id]["Shifts_over_six_hours"] += 1

        event_iso_year, event_iso_week, _ = event_date.isocalendar()
        week_key = f"{event_iso_year}-W{event_iso_week:02d}"
        dict_employees[emp_id]["Shifts_per_week"][week_key] = (
            dict_employees[emp_id]["Shifts_per_week"].get(week_key, 0) + 1)

        return {
            "EventID": event_id,
            "EmployeeID": emp_id,
            "RoleID": role_id,
            "ShiftStart": shift_begins,
            "ShiftEnd": shift_ends,
            "ShiftHours": total_shift_hours,
            "AddedScore": event_score,
            "NewScore": dict_employees[emp_id]["Score"],
        }

    def event_is_fully_staffed(event_id: int, event_state: dict) -> bool:
        return all(role["filled_by"] is not None for role in event_state[event_id]["roles"])

    # Upphafsstilla event_state
    event_state = {}
    for event_id in dict_events:
        event_state[event_id] = {
            "roles": build_event_roles(event_id)}

    all_work_results = []

    # Aðallykkja:
    # 1. finna starfsmann efst í forgangi
    # 2. finna bestu vakt/hlutverk fyrir hann
    # 3. úthluta
    # 4. endurtaka
    while not all(all(r["filled_by"] is not None for r in state["roles"]) for state in event_state.values()):
        progress = False

        employees_sorted = sorted(dict_employees.keys(), key=employee_priority)

        for emp_id in employees_sorted:
            best_option = choose_best_role_for_employee(emp_id, event_state)

            if best_option is None:
                continue

            event_id = best_option["event_id"]
            role_id = best_option["role_id"]

            result = assign_employee_to_role(emp_id, event_id, role_id, event_state)
            all_work_results.append(result)

            progress = True
            break

        if not progress:
            unfilled = {
                event_id: [
                    role for role in event_state[event_id]["roles"]
                    if role["filled_by"] is None
                ]
                for event_id in event_state
                if not event_is_fully_staffed(event_id, event_state)}

            raise ValueError(
                f"Ekki tókst að manna öll hlutverk. Ófyllt staða: {unfilled}")

    # Lokatékk á fullmönnuðum hópum
    for event_id in event_state:
        final_team = [
            role["filled_by"]
            for role in event_state[event_id]["roles"]
            if role["filled_by"] is not None]

        if not is_valid_final_team(final_team):
            raise ValueError(
                f"Ólöglegur lokahópur fyrir Event {event_id}. Valdir: {final_team}")

    return all_work_results, event_state