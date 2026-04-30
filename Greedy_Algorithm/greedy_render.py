import os
from collections import defaultdict
from open_excel import (
    open_excel,
    open_previous_scores,
    open_previous_stats,
    merge_scores_into_employees,
    merge_previous_stats_into_employees,
)
from pick_employees import assign_all_events
from Export_Json_Greedy import Export_Json
from export_schedule_to_excel_greedy import export_schedule_to_excel
import traceback


def run_greedy(input_path):

    try:
        # =========================
        # Extract name
        # =========================
        filename = os.path.basename(input_path)
        month = os.path.splitext(filename)[0]

        os.makedirs("Data", exist_ok=True)

        # =========================
        # Initialize
        # =========================
        hours_per_employee = defaultdict(float)
        daily_hours_per_employee = defaultdict(float)
        assigned_shifts = defaultdict(list)
        employee_worked_days = defaultdict(set)

        max_daily_hours = 11
        max_weekly_hours = 48
        min_rest_hours = 13
        base_min_shifts = 3

        # =========================
        # Load Excel
        # =========================
        dict_events, dict_employees, employees_days_off, score_rules, skillset_scores, event_requests = open_excel(
            filename,
            "Events",
            "Employees",
            "DaysOff",
            "ScoreKeys",
            "SkillsetScores",
            "EventReq"
        )

        # =========================
        # Previous data
        # =========================
        prev_dict = os.path.join("Data", f"{month}_output_dicts.json")
        prev_list = os.path.join("Data", f"{month}_output_list.json")

        if os.path.exists(prev_dict) and os.path.exists(prev_list):
            previous_scores = open_previous_scores(prev_dict)
            previous_stats = open_previous_stats(prev_dict, prev_list)

            dict_employees = merge_scores_into_employees(dict_employees, previous_scores)
            dict_employees = merge_previous_stats_into_employees(dict_employees, previous_stats)

        # =========================
        # Run greedy
        # =========================
        rows, _ = assign_all_events(
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

        # =========================
        # Export JSON
        # =========================
        Export_Json(dict_employees, dict_events, rows, month)

        # =========================
        # Export Excel
        # =========================
        period_start = min(e["Date"] for e in dict_events.values())
        period_end = max(e["Date"] for e in dict_events.values())

        output_file = os.path.join("Data", f"{month}_schedule.xlsx")

        export_schedule_to_excel(
            rows,
            dict_events,
            dict_employees,
            output_file,
            period_start,
            period_end
        )

        return {
            "status": "success",
            "output_file": output_file
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }