
from open_excel_new import open_excel, open_previous_scores, open_previous_stats, merge_scores_into_employees, merge_previous_stats_into_employees
from pick_employees_new import assign_all_events
from Print_Results_Greedy import Print_Results_Greedy
from Export_Json_Greedy import Export_Json
from export_schedule_to_excel_greedy import export_schedule_to_excel
from collections import defaultdict


def run_greedy(input_file, month="04_26"):

    # Upphafsstilla breytur
    hours_per_employee = defaultdict(float)
    daily_hours_per_employee = defaultdict(float)
    score_per_employee = defaultdict(float)
    assigned_shifts = defaultdict(list)
    shifts_per_employee = defaultdict(int)
    employee_worked_days = defaultdict(set)

    max_daily_hours = 11
    max_weekly_hours = 48
    min_rest_hours = 13
    base_min_shifts = 3

    # -------------------------
    # Load data
    # -------------------------
    dict_events, dict_employees, employees_days_off, score_rules, skillset_scores, event_requests = open_excel(
        input_file, "Events", "Employees", "DaysOff", "ScoreKeys", "SkillsetScores", "EventReq"
    )

    # -------------------------
    # Load previous data
    # -------------------------
    previous_json_dict = "02_26_output_dicts.json"
    previous_json_list = "02_26_output_list.json"

    previous_scores = open_previous_scores(previous_json_dict)
    previous_stats = open_previous_stats(previous_json_dict, previous_json_list)

    dict_employees = merge_scores_into_employees(dict_employees, previous_scores)
    dict_employees = merge_previous_stats_into_employees(dict_employees, previous_stats)

    rows = []

    # -------------------------
    # Run greedy
    # -------------------------
    try:
        rows, event_state = assign_all_events(
            dict_events,
            dict_employees,
            hours_per_employee,
            employees_days_off,
            daily_hours_per_employee,
            max_daily_hours,
            max_weekly_hours,
            assigned_shifts,
            min_rest_hours,
            employee_worked_days,
            score_rules,
            skillset_scores,
            event_requests,
            base_min_shifts
        )
    except Exception as e:
        return {"error": str(e)}

    # -------------------------
    # Export JSON
    # -------------------------
    Export_Json(dict_employees, dict_events, rows, month)

    # -------------------------
    # Export Excel
    # -------------------------
    period_start = min(event["Date"] for event in dict_events.values())
    period_end = max(event["Date"] for event in dict_events.values())

    output_file = f"{month}_schedule_results.xlsx"

    export_schedule_to_excel(
        rows,
        dict_events,
        dict_employees,
        output_file,
        period_start=period_start,
        period_end=period_end
    )

    return {"file": output_file}