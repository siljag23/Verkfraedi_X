
from Greedy_Algorithm.def_for_pick_employees import build_event_roles, is_valid_final_team, employee_priority, choose_best_role_for_employee, assign_employee_to_role, event_is_fully_staffed, get_event_datetime_info, lookup_score


def assign_all_events(dict_events, dict_employees, hours_per_employee, employee_days_off, daily_hours_per_employee, max_daily_hours, max_weekly_hours, 
                      assigned_shifts, min_rest_hours, employee_worked_days, score_rules, skillset_scores, event_requests, base_min_shifts):
    """
    Main function:

    selects an employee based on priority
    finds the best available shift/role for that employee
    assigns the shift
    repeats until all shifts are filled or no further assignments can be made

    Returns:

    all_work_results: list of all assignments
    event_state: status of all events after assignment
    """

    # Calculate the period for the 48-hour weekly average rule
    all_event_dates = [ev["Date"] for ev in dict_events.values()]
    period_start = min(all_event_dates)
    period_end = max(all_event_dates)

    period_days = (period_end - period_start).days + 1
    period_weeks = period_days / 7
    if period_weeks <= 0:
        period_weeks = 1

    # Calculate minimum shifts based on availability - employees with no days off should get at least 3 shifts
    for emp_id in dict_employees:
        ratio = dict_employees[emp_id].get("Availability_ratio", 1.0)
        dict_employees[emp_id]["min_shifts"] = round(base_min_shifts * ratio)

    # Initialize event_state
    event_state = {}
    for event_id in dict_events:
        event_state[event_id] = {
            "roles": build_event_roles(event_id, dict_events)}

    all_work_results = []

    # Main loop:
    # 1. find employee with highest priority
    # 2. find best available shift/role for them
    # 3. assign the shift
    # 4. repeat
    while not all(all(r["filled_by"] is not None for r in state["roles"]) for state in event_state.values()):
        progress = False

        employees_sorted = sorted(dict_employees.keys(),
            key=lambda emp_id: employee_priority(emp_id, dict_employees, hours_per_employee, base_min_shifts))

        for emp_id in employees_sorted:
            best_option = choose_best_role_for_employee(emp_id, event_state, dict_events, employee_days_off, employee_worked_days, daily_hours_per_employee, max_daily_hours,
                                hours_per_employee, period_weeks, max_weekly_hours, min_rest_hours, assigned_shifts, dict_employees, score_rules, skillset_scores, event_requests)

            if best_option is None:
                continue

            event_id = best_option["event_id"]
            role_id = best_option["role_id"]

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

    # Final check for fully staffed teams and valid employee assignments
    for event_id in event_state:
        final_team = [
            role["filled_by"]
            for role in event_state[event_id]["roles"]
            if role["filled_by"] is not None]

        if not is_valid_final_team(final_team, dict_employees):
            raise ValueError(
                f"Ólöglegur lokahópur fyrir Event {event_id}. Valdir: {final_team}")

    return all_work_results, event_state
    