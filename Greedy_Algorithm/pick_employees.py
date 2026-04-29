
from def_for_pick_employees import build_event_roles, is_valid_final_team, employee_priority, choose_best_role_for_employee, assign_employee_to_role, event_is_fully_staffed, get_event_datetime_info, lookup_score


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
        ratio = dict_employees[emp_id].get("Availability_ratio", 1.0)
        dict_employees[emp_id]["min_shifts"] = round(base_min_shifts * ratio)

    # Upphafsstilla event_state
    event_state = {}
    for event_id in dict_events:
        event_state[event_id] = {
            "roles": build_event_roles(event_id, dict_events)}

    all_work_results = []

    # Aðallykkja:
    # 1. finna starfsmann efst í forgangi
    # 2. finna bestu vakt/hlutverk fyrir hann
    # 3. úthluta
    # 4. endurtaka
    while not all(all(r["filled_by"] is not None for r in state["roles"]) for state in event_state.values()):
        progress = False

        employees_sorted = sorted(dict_employees.keys(),
            key=lambda emp_id: employee_priority(emp_id, dict_employees, hours_per_employee, base_min_shifts))
        """
        # 1. Prenta forgangsröðun
        print(f"\n{'='*70}")
        print(f"{'Starfsmaður':<20} {'Completion':>12} {'Vaktir':>8} {'Min':>6} {'Stig':>10}")
        print("-" * 70)
        for emp_id in employees_sorted:
            name = dict_employees[emp_id].get("EmployeeName", str(emp_id))
            current = dict_employees[emp_id]["Number_of_shifts"]
            min_s = dict_employees[emp_id].get("min_shifts", base_min_shifts)
            ratio = current / min_s if min_s > 0 else 1.0
            score = dict_employees[emp_id]["Score"]
            print(f"{name:<20} {ratio:>12.2f} {current:>8} {min_s:>6} {score:>10.1f}")
        """

        for emp_id in employees_sorted:
            best_option = choose_best_role_for_employee(emp_id, event_state, dict_events, employee_days_off, employee_worked_days, daily_hours_per_employee, max_daily_hours,
                                hours_per_employee, period_weeks, max_weekly_hours, min_rest_hours, assigned_shifts, dict_employees, score_rules, skillset_scores, event_requests)

            if best_option is None:
                continue

            event_id = best_option["event_id"]
            role_id = best_option["role_id"]
            """
            # ------ Print -------
            event = dict_events[event_id]
            datetime_info = get_event_datetime_info(event_id, dict_events)
            event_date = datetime_info["event_date"]
            total_shift_hours = datetime_info["total_shift_hours"]
            hall = event.get("Hall")
            category = event["EventCategory"]
            required_skill = next(r["required_skill"] for r in event_state[event_id]["roles"] if r["role_id"] == role_id)

            weekend_count = dict_employees[emp_id]["Shifts_on_weekends"]
            prev_weekend_count = dict_employees[emp_id]["prev_weekend_shifts"]
            hall_count = dict_employees[emp_id].get("Shifts_per_hall", {}).get(hall, 0)
            event_iso_year, event_iso_week, _ = event_date.isocalendar()
            week_key = f"{event_iso_year}-W{event_iso_week:02d}"
            shifts_this_week = dict_employees[emp_id].get("Shifts_per_week", {}).get(week_key, 0)
            shift_length_key = int(round(total_shift_hours))
            same_length = dict_employees[emp_id].get("Shifts_per_length", {}).get(shift_length_key, 0)
            over_six = dict_employees[emp_id]["Shifts_over_six_hours"]
            category_count = dict_employees[emp_id].get("current_shifts_per_category", {}).get(category, 0)
            emp_skill = dict_employees[emp_id]["Skillset"]

            event_score = event["EventRanking"]
            weekend_adj = lookup_score(score_rules.get("Weekend", {}), weekend_count, 0) if event_date.weekday() in [4,5,6] else 0
            weekend_last_adj = lookup_score(score_rules.get("Weekend_last_period", {}), prev_weekend_count, 0) if event_date.weekday() in [4,5,6] else 0
            hall_adj = lookup_score(score_rules.get("Hall", {}), hall_count, 0) if hall else 0
            week_adj = lookup_score(score_rules.get("Shifts_this_week", {}), shifts_this_week, 0)
            length_adj = lookup_score(score_rules.get("Shifts_this_length", {}), same_length, 0)
            over_six_adj = lookup_score(score_rules.get("Shift_over_six_hours", {}), over_six, 0) if total_shift_hours > 6 else 0
            category_adj = lookup_score(score_rules.get("Category", {}), category_count, 0) if category else 0
            skill_adj = skillset_scores.get(required_skill, {}).get(emp_skill, 0) if required_skill else 0
            req_adj = lookup_score(score_rules.get("Req_this_shift", {}), 1, 0) if (emp_id, event_id) in event_requests else 0
            total = event_score + weekend_adj + weekend_last_adj + hall_adj + week_adj + length_adj + over_six_adj + category_adj + skill_adj + req_adj

            name = dict_employees[emp_id].get("EmployeeName", str(emp_id))

            # 2. Prenta persónuleg stig
            print(f"\n>>> Úthluta: {name} -> Event {event_id} ({event.get('Event', '')})")
            print(f"  {'EventRanking':<30} {event_score:>8.1f}")
            print(f"  {'Weekend':<30} {weekend_adj:>8.1f}  (fjöldi: {weekend_count})")
            print(f"  {'Weekend síðasti':<30} {weekend_last_adj:>8.1f}  (fjöldi: {prev_weekend_count})")
            print(f"  {'Hall':<30} {hall_adj:>8.1f}  (fjöldi: {hall_count})")
            print(f"  {'Shifts þessari viku':<30} {week_adj:>8.1f}  (fjöldi: {shifts_this_week})")
            print(f"  {'Shift lengd':<30} {length_adj:>8.1f}  (fjöldi: {same_length})")
            print(f"  {'Shift yfir 6h':<30} {over_six_adj:>8.1f}  (fjöldi: {over_six})")
            print(f"  {'Category':<30} {category_adj:>8.1f}  (fjöldi: {category_count})")
            print(f"  {'Skillset':<30} {skill_adj:>8.1f}  (req: {required_skill}, emp: {emp_skill})")
            print(f"  {'Request':<30} {req_adj:>8.1f}")
            print(f"  {'Heildarstig':<30} {total:>8.1f}")
            
            # ------ Print búið ------
            """
            result = assign_employee_to_role(emp_id, event_id, role_id, event_state, dict_events, hours_per_employee, 
                            employee_worked_days, daily_hours_per_employee, assigned_shifts, dict_employees)
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

        if not is_valid_final_team(final_team, dict_employees):
            raise ValueError(
                f"Ólöglegur lokahópur fyrir Event {event_id}. Valdir: {final_team}")

    return all_work_results, event_state
    