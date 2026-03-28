from datetime import datetime, timedelta, time
from shift_length import shift_length
import math


def assign_all_events(dict_events, dict_employees, hours_per_employee, employee_days_off, daily_hours_per_employee,
                      max_daily_hours, assigned_shifts, min_rest_hours, employee_worked_days, score_rules, skillset_scores):
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

    def parse_event_date(ev):
        """Les dagsetningu úr event dict og skilar henni sem date object"""
        raw = ev["Date"]
        if isinstance(raw, str):
            return datetime.strptime(raw.strip(), "%d.%m.%Y").date()
        elif hasattr(raw, "date"):
            return raw.date()
        return raw

    def ensure_time(x):
        """Breytum dagsetningum á röngu formi í datetime.time"""
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

    def to_int(x, default=0):
        """Breytum gildum í heiltölu"""
        if x is None:
            return default
        if isinstance(x, float) and math.isnan(x):
            return default
        try:
            return int(x)
        except:
            return default

    def to_number(x, default=0):
        """Breytum gildum í brotatölu"""
        if x is None:
            return default
        if isinstance(x, float) and math.isnan(x):
            return default
        try:
            return float(x)
        except:
            return default

    def clean_str(x):
        if x is None:
            return ""
        s = str(x).strip()
        return "" if s.lower() == "nan" else s

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

    def emp_skill(emp_id: int) -> int:
        """Breytum skillset starsfmanna í heiltölu"""
        return to_int(dict_employees[emp_id].get("Skillset", 0), 0)

    # Reiknum tímabil fyrir 48 klst/viku meðaltalsreglu
    all_event_dates = [parse_event_date(ev) for ev in dict_events.values()]
    period_start = min(all_event_dates)
    period_end = max(all_event_dates)

    period_days = (period_end - period_start).days + 1
    period_weeks = period_days / 7
    if period_weeks <= 0:
        period_weeks = 1

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

        shift_begins_time = ensure_time(event["ShiftBegins"])
        shift_ends_time = ensure_time(event["ShiftEnds"])

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
        Býr til hlutverk/sæti fyrir event.

        Dæmi:
        Employees=4, Skillset1=1, Skillset2=1
        =>
        [
            {"role_id": 0, "required_skill": 1},
            {"role_id": 1, "required_skill": 2},
            {"role_id": 2, "required_skill": None},
            {"role_id": 3, "required_skill": None},
        ]
        """
        event = dict_events[event_id]

        req_employees = to_int(event.get("Employees"), 0)
        req_skillset_1 = to_int(event.get("Skillset1"), 0)
        req_skillset_2 = to_int(event.get("Skillset2"), 0)

        if req_skillset_1 + req_skillset_2 > req_employees:
            raise ValueError(
                f"Skillset1 + Skillset2 ({req_skillset_1 + req_skillset_2}) > Employees ({req_employees}) fyrir Event {event_id}")

        roles = []
        role_id = 0

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
        """Athugar hvort starfsmenn uppfylli lágmarks hvíldartíma"""
        rest_delta = timedelta(hours=min_rest_hours)

        for old_begins, old_ends in assigned_shifts.get(emp_id, []):
            ok = (shift_begins >= old_ends + rest_delta) or (old_begins >= shift_ends + rest_delta)
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
        """Almenn gjaldgengni starfsmanns fyrir event, óháð því hvaða hlutverk innan vaktar er valið"""
        info = get_event_datetime_info(event_id)

        event_date = info["event_date"]
        shift_begins = info["shift_begins"]
        shift_ends = info["shift_ends"]
        total_shift_hours = info["total_shift_hours"]
        day_1 = info["day_1"]
        day_2 = info["day_2"]
        hours_day_1 = info["hours_day_1"]
        hours_day_2 = info["hours_day_2"]
        blocked_days = info["blocked_days"]

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
        if avg_weekly_hours > 48:
            return False

        if not respects_min_rest(emp_id, shift_begins, shift_ends):
            return False

        return True

    def is_valid_final_team(event_id: int, employee_ids: list[int]) -> bool:
        """
        Lokatékk á hópnum þegar event er fullmannað.

        Núverandi regla:
        - ef einhver skillset 3 er í hópnum, þá má hópurinn ekki eingöngu vera skillset 3
        """
        if not employee_ids:
            return True

        skills = [emp_skill(emp_id) for emp_id in employee_ids]

        if 3 in skills and all(skill == 3 for skill in skills):
            return False

        return True

    def employee_priority(emp_id: int):
        """Raðar starfsmönnum í forgangsröð, lægstu stig efst"""
        return (
            to_number(dict_employees[emp_id].get("Score", 0), 0),
            to_int(dict_employees[emp_id].get("Number_of_shifts", 0), 0),
            to_number(hours_per_employee.get(emp_id, 0), 0),
            emp_id
        )

    def personal_role_score(emp_id: int, event_id: int, role: dict) -> float:
        """
        Persónulegt val-score fyrir starfsmann á tiltekið hlutverk á tilteknum event.

        HÆRRA score = betra val fyrir þennan starfsmann.

        Þetta score er aðeins notað við valið.
        Þegar starfsmaður er úthlutaður fær hann samt upprunaleg EventRanking stig.
        """
        event = dict_events[event_id]
        datetime_info = get_event_datetime_info(event_id)
        event_date = datetime_info["event_date"]
        total_shift_hours = datetime_info["total_shift_hours"]

        hall = clean_str(event.get("Hall"))

        event_score = to_number(event.get("EventRanking", 0), 0)
        current_shifts = to_int(dict_employees[emp_id].get("Number_of_shifts", 0), 0)
        weekend_count = to_int(dict_employees[emp_id].get("Shifts_on_weekends", 0), 0)

        hall_count = to_int(
            dict_employees[emp_id].get("Shifts_per_hall", {}).get(hall, 0), 0)

        emp_current_skill = emp_skill(emp_id)
        required_skill = role.get("required_skill")

        # =========================
        # Score úr ScoreKeys
        # =========================

        # Helgarvakt í núverandi tímabili
        weekend_adjustment = 0
        if event_date.weekday() in [4, 5, 6]:
            weekend_adjustment = lookup_score(
                score_rules.get("Weekend", {}), weekend_count, 0)

        # Helgarvaktir frá síðasta tímabili
        prev_weekend_count = to_int(
            dict_employees[emp_id].get("prev_weekend_shifts", 0), 0)
        weekend_last_period_adjustment = 0
        if event_date.weekday() in [4, 5, 6]:
            weekend_last_period_adjustment = lookup_score(
                score_rules.get("Weekend_last_period", {}), prev_weekend_count, 0)

        # Fjöldi vakta í sama sal
        hall_adjustment = 0
        if hall:
            hall_adjustment = lookup_score(
                score_rules.get("Hall", {}), hall_count, 0)

        # Fjöldi vakta í þessari viku
        shifts_this_week = current_shifts
        shifts_this_week_adjustment = lookup_score(
            score_rules.get("Shifts_this_week", {}), shifts_this_week, 0)

        # Fjöldi vakta af þessari lengd
        shift_length_key = int(round(total_shift_hours))

        current_count_same_length = to_int(
            dict_employees[emp_id].get("Shifts_per_length", {}).get(shift_length_key, 0), 0
        )

        shift_length_adjustment = lookup_score(
            score_rules.get("Shifts_this_length", {}),
            current_count_same_length, 0)

        # Fjöldi vakta 6+ klst.
        shift_over_six_hours_adjustment = 0

        if total_shift_hours > 6:
            current_over_six_count = to_int(
                dict_employees[emp_id].get("Shifts_over_six_hours", 0), 0
            )

            shift_over_six_hours_adjustment = lookup_score(
                score_rules.get("Shift_over_six_hours", {}),
                current_over_six_count, 0)

        # =========================
        # Skillset score úr SkillsetScores
        # =========================
        skill_adjustment = 0
        if required_skill is not None:
            skill_adjustment = skillset_scores.get(required_skill, {}).get(emp_current_skill, 0)

        return (
            event_score
            + weekend_adjustment
            + weekend_last_period_adjustment
            + hall_adjustment
            + shifts_this_week_adjustment
            + shift_length_adjustment
            + shift_over_six_hours_adjustment
            + skill_adjustment
        )

    def can_take_role(emp_id: int, event_id: int, role: dict, event_state: dict) -> bool:
        """Athugar hvort starfsmaður megi taka ákveðið hlutverk á ákveðnum event"""
        if role["filled_by"] is not None:
            return False

        if not is_eligible_for_event(emp_id, event_id):
            return False

        current_team = [
            r["filled_by"]
            for r in event_state[event_id]["roles"]
            if r["filled_by"] is not None
        ]
        projected_team = current_team + [emp_id]
        if not is_valid_final_team(event_id, projected_team):
            return False

        return True

    def choose_best_role_for_employee(emp_id: int, event_state: dict):
        """
        Finnur besta lausa hlutverkið fyrir starfsmann yfir alla eventa.

        Skilar t.d.
        {
            "event_id": 15,
            "role_id": 2,
            "score": 11.5
        }
        """
        best_option = None

        for event_id, state in event_state.items():
            for role in state["roles"]:
                if not can_take_role(emp_id, event_id, role, event_state):
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
        info = get_event_datetime_info(event_id)

        hall = clean_str(event.get("Hall"))
        category = clean_str(event.get("EventCategory"))

        event_date = info["event_date"]
        shift_begins = info["shift_begins"]
        shift_ends = info["shift_ends"]
        total_shift_hours = info["total_shift_hours"]
        day_1 = info["day_1"]
        day_2 = info["day_2"]
        hours_day_1 = info["hours_day_1"]
        hours_day_2 = info["hours_day_2"]
        blocked_days = info["blocked_days"]

        event_score = to_number(event.get("EventRanking", 0), 0)

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

        # ATH: hér fær starfsmaður upprunaleg event-stig, ekki personal_role_score
        dict_employees[emp_id]["Score"] = to_number(
            dict_employees[emp_id].get("Score", 0), 0) + event_score

        dict_employees[emp_id]["Number_of_shifts"] = (
            to_int(dict_employees[emp_id].get("Number_of_shifts"), 0) + 1)

        if event_date.weekday() in [4, 5, 6]:
            dict_employees[emp_id]["Shifts_on_weekends"] = (
                to_int(dict_employees[emp_id].get("Shifts_on_weekends"), 0) + 1)

        if hall:
            if "Shifts_per_hall" not in dict_employees[emp_id] or not isinstance(dict_employees[emp_id]["Shifts_per_hall"], dict):
                dict_employees[emp_id]["Shifts_per_hall"] = {}

            current_hall_count = to_int(
                dict_employees[emp_id]["Shifts_per_hall"].get(hall, 0), 0)
            dict_employees[emp_id]["Shifts_per_hall"][hall] = current_hall_count + 1

        if category:
            if (
                "current_shifts_per_category" not in dict_employees[emp_id]
                or not isinstance(dict_employees[emp_id]["current_shifts_per_category"], dict)):
                dict_employees[emp_id]["current_shifts_per_category"] = {}

            current_cat_count = to_int(
                dict_employees[emp_id]["current_shifts_per_category"].get(category, 0), 0)
            dict_employees[emp_id]["current_shifts_per_category"][category] = current_cat_count + 1

        # Fjöldi vakta per lengd
        if (
            "Shifts_per_length" not in dict_employees[emp_id]
            or not isinstance(dict_employees[emp_id]["Shifts_per_length"], dict)
        ):
            dict_employees[emp_id]["Shifts_per_length"] = {}

        shift_length_key = int(round(total_shift_hours))
        current_length_count = to_int(
            dict_employees[emp_id]["Shifts_per_length"].get(shift_length_key, 0), 0
        )
        dict_employees[emp_id]["Shifts_per_length"][shift_length_key] = current_length_count + 1

        # Fjöldi vakta yfir 6 klst
        if total_shift_hours > 6:
            dict_employees[emp_id]["Shifts_over_six_hours"] = (
                to_int(dict_employees[emp_id].get("Shifts_over_six_hours", 0), 0) + 1
            )

        return {
            "EventID": event_id,
            "EmployeeID": emp_id,
            #"EmployeeName": dict_employees[emp_id].get("EmployeeName"),
            #"EmployeeSkillset": dict_employees[emp_id].get("Skillset"),
            "RoleID": role_id,
            "ShiftStart": shift_begins,
            "ShiftEnd": shift_ends,
            "ShiftHours": total_shift_hours,
            #"TotalHours": hours_per_employee[emp_id],
            "AddedScore": event_score,
            "NewScore": dict_employees[emp_id]["Score"],
            #"NumberOfShifts": dict_employees[emp_id]["Number_of_shifts"],
            #"ShiftsOnWeekends": dict_employees[emp_id]["Shifts_on_weekends"],
            #"ShiftsPerHall": dict_employees[emp_id]["Shifts_per_hall"].get(hall, 0) if hall else 0,
            #"CurrentShiftsPerCategory": dict_employees[emp_id]["current_shifts_per_category"].get(category, 0) if category else 0
            }

    def event_is_fully_staffed(event_id: int, event_state: dict) -> bool:
        return all(role["filled_by"] is not None for role in event_state[event_id]["roles"])

    def all_events_fully_staffed(event_state: dict) -> bool:
        return all(event_is_fully_staffed(event_id, event_state) for event_id in event_state)

    # Upphafsstilla Score sem tölugildi
    for emp_id in dict_employees:
        dict_employees[emp_id]["Score"] = to_number(
            dict_employees[emp_id].get("Score", 0), 0)

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
    while not all_events_fully_staffed(event_state):
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

        if not is_valid_final_team(event_id, final_team):
            raise ValueError(
                f"Ólöglegur lokahópur fyrir Event {event_id}. Valdir: {final_team}")

    return all_work_results, event_state