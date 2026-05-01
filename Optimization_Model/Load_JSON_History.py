import json
import pandas as pd

def Load_JSON_History(list_file, dict_file):

    hist_shifts = {}
    hist_hours = {}
    hist_scores = {}
    hist_weekend = {}

    try:
        with open(list_file, "r", encoding="utf-8") as f:
            assignment_list = json.load(f)

        with open(dict_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    except FileNotFoundError:
        print("No history file found")
        return {}, {}, {}, {}

    events_dict = data["events"]

    for (j, i) in assignment_list:

        j = str(j)  # 🔥 mjög mikilvægt

        if j not in events_dict:
            continue

        event = events_dict[j]

        # -------------------------
        # SHIFTS
        # -------------------------
        hist_shifts[i] = hist_shifts.get(i, 0) + 1

        # -------------------------
        # HOURS (compute duration)
        # -------------------------
        start = pd.to_datetime(event["ShiftBegins"])
        end = pd.to_datetime(event["ShiftEnds"])

        duration = (end - start).total_seconds() / 3600
        if duration < 0:
            duration += 24

        hist_hours[i] = hist_hours.get(i, 0) + duration

        # -------------------------
        # SCORE
        # -------------------------
        hist_scores[i] = hist_scores.get(i, 0) + event["EventRanking"]

        # -------------------------
        # WEEKEND
        # -------------------------
        date = pd.to_datetime(event["Date"])

        if date.weekday() in [4,5,6]:
            hist_weekend[i] = hist_weekend.get(i, 0) + 1

    return hist_shifts, hist_hours, hist_scores, hist_weekend