import json
import pandas as pd

def Load_JSON_History(
    filename,
    dict_events,
    shift_dur,
    shift_score
):

    hist_shifts = {}
    hist_hours = {}
    hist_scores = {}
    hist_weekend = {}

    try:
        with open(filename, "r", encoding="utf-8") as f:
            assignment_list = json.load(f)
    except FileNotFoundError:
        print(f"No history file found: {filename}")
        return {}, {}, {}, {}

    for (j, i) in assignment_list:

        hist_shifts[i] = hist_shifts.get(i, 0) + 1
        hist_hours[i] = hist_hours.get(i, 0) + shift_dur[j]
        hist_scores[i] = hist_scores.get(i, 0) + shift_score[j]

        date = pd.to_datetime(dict_events[j]["Date"], dayfirst=True)

        if date.weekday() in [4,5,6]:
            hist_weekend[i] = hist_weekend.get(i, 0) + 1

    return hist_shifts, hist_hours, hist_scores, hist_weekend