import json
import pandas as pd
from Optimization_Model.Compute_Shift_Duration import To_Hours

def Load_JSON_History(list_file, dict_file):

    hist_shifts = {}
    hist_hours = {}
    hist_scores = {}
    hist_weekend = {}
    hist_availability = {}

    try:
        with open(list_file, "r", encoding="utf-8") as f:
            assignment_list = json.load(f)

        with open(dict_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    except FileNotFoundError:
        print("No history file found")
        return {}, {}, {}, {}, {}

    events_dict = data["events"]
    employees_dict = data["employees"]

    # -------------------------
    # LOAD AVAILABILITY
    # -------------------------
    for i in employees_dict:
        hist_availability[int(i)] = employees_dict[i].get("Availability", 1.0)

    # -------------------------
    # LOOP ASSIGNMENTS
    # -------------------------
    for (j, i) in assignment_list:
        i = int(i)
        j = str(j)

        if j not in events_dict:
            continue

        event = events_dict[j]

        # shifts
        hist_shifts[i] = hist_shifts.get(i, 0) + 1

        # hours
        start_h = To_Hours(event["ShiftBegins"])
        end_h = To_Hours(event["ShiftEnds"])

        duration = end_h - start_h
        if duration < 0:
            duration += 24

        hist_hours[i] = hist_hours.get(i, 0) + duration

        # score
        hist_scores[i] = hist_scores.get(i, 0) + event["EventRanking"]

        # weekend
        date = pd.to_datetime(event["Date"])
        if date.weekday() in [4,5,6]:
            hist_weekend[i] = hist_weekend.get(i, 0) + 1

    return hist_shifts, hist_hours, hist_scores, hist_weekend, hist_availability