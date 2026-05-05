import numpy as np
import pandas as pd

def Total_Stats(
    employees,
    events,
    works,
    dict_events,
    shift_dur,
    curr_availability,
    hist_shifts=None,
    hist_hours=None,
    hist_scores=None,
    hist_weekend=None,
    hist_availability=None   
):

    hist_shifts = hist_shifts or {}
    hist_hours = hist_hours or {}
    hist_scores = hist_scores or {}
    hist_weekend = hist_weekend or {}
    hist_availability = hist_availability or {}

    # -------------------------
    # Weekend lookup
    # -------------------------
    is_weekend = {}
    for j in events:
        d = pd.to_datetime(dict_events[j]["Date"], dayfirst=True)
        is_weekend[j] = 1 if d.weekday() in [4, 5, 6] else 0

    raw_current = {}
    raw_history = {}
    raw_total = {}
    norm_current = {}
    norm_history = {}
    norm_total = {}

    # -------------------------
    # RAW
    # -------------------------
    for i in employees:

        shifts_i = sum(works[i, j].X for j in events)
        hours_i = sum(works[i, j].X * shift_dur[j] for j in events)
        weekend_i = sum(works[i, j].X * is_weekend[j] for j in events)
        score_i = sum(
            works[i, j].X * dict_events[j]["EventRanking"]
            for j in events
        )

        raw_current[i] = {
            "shifts": shifts_i,
            "hours": hours_i,
            "weekend": weekend_i,
            "score": score_i,
        }

        raw_history[i] = {
            "shifts": hist_shifts.get(i, 0),
            "hours": hist_hours.get(i, 0),
            "weekend": hist_weekend.get(i, 0),
            "score": hist_scores.get(i, 0),
        }

        raw_total[i] = {
            "shifts": hist_shifts.get(i, 0) + shifts_i,
            "hours": hist_hours.get(i, 0) + hours_i,
            "weekend": hist_weekend.get(i, 0) + weekend_i,
            "score": hist_scores.get(i, 0) + score_i,
        }

    # -------------------------
    # NORMALIZED
    # -------------------------
    for i in employees:

        curr_avail = curr_availability.get(i,0)
        hist_avail = hist_availability.get(i,0)

        if curr_avail > 0:
            norm_current[i] = {
                "shifts": raw_current[i]["shifts"] / curr_avail,
                "hours": raw_current[i]["hours"] / curr_avail,
                "weekend": raw_current[i]["weekend"] / curr_avail,
                "score": raw_current[i]["score"] / curr_avail,
            }

        if hist_avail > 0:
            norm_history[i] = {
                "shifts": hist_shifts.get(i, 0) / hist_avail,
                "hours": hist_hours.get(i, 0) / hist_avail,
                "weekend": hist_weekend.get(i, 0) / hist_avail,
                "score": hist_scores.get(i, 0) / hist_avail,
            }

        if curr_avail > 0 or hist_avail > 0:

            total_avail = curr_avail + hist_avail

            if total_avail > 0:
                norm_total[i] = {
                    "shifts": raw_total[i]["shifts"] / total_avail,
                    "hours": raw_total[i]["hours"] / total_avail,
                    "weekend": raw_total[i]["weekend"] / total_avail,
                    "score": raw_total[i]["score"] / total_avail,
                }

    return raw_current, raw_total, norm_current, norm_total, norm_history, raw_history


def Print_Stats(title, data, filter_zero=False):

    print(f"\n--- {title} ---")

    metrics = ["shifts", "hours", "weekend", "score"]

    for key in metrics:

        values = [
            data[i][key]
            for i in data
            if key in data[i] and (data[i]["shifts"] > 0 if filter_zero else True)
        ]

        if len(values) == 0:
            print(f"\n{key}: No data")
            continue

        v = np.array(values, dtype=float)

        print(f"\n{key}:")
        print("  Min:", round(v.min(), 2))
        print("  Max:", round(v.max(), 2))
        print("  Avg:", round(v.mean(), 2))
        print("  Std:", round(v.std(), 2))