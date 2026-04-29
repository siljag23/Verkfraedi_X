import numpy as np
import pandas as pd


def Total_Stats(
    employees,
    events,
    works,
    dict_events,
    dict_employees,
    employee_days,
    shift_dur,
    hist_shifts=None,
    hist_hours=None,
    hist_scores=None,
    hist_weekend=None,
    min_avail_floor=0.1
):
    # -------------------------
    # Defaults
    # -------------------------
    hist_shifts = hist_shifts or {}
    hist_hours = hist_hours or {}
    hist_scores = hist_scores or {}
    hist_weekend = hist_weekend or {}

    # -------------------------
    # Availability (robust – only uses dict_events)
    # -------------------------
    total_days = len(
        set(
            pd.to_datetime(dict_events[j]["Date"], dayfirst=True).date()
            for j in events
        )
    )

    availability = {}
    for i in employees:
        days_off = employee_days.get(i, set())
        availability[i] = (
            (total_days - len(days_off)) / total_days
            if total_days > 0 else 1.0
        )

    # -------------------------
    # Weekend lookup (robust)
    # -------------------------
    is_weekend = {}
    for j in events:
        d = pd.to_datetime(dict_events[j]["Date"], dayfirst=True)
        is_weekend[j] = 1 if d.weekday() in [4, 5, 6] else 0

    # -------------------------
    # Containers (NORMALIZED ONLY)
    # -------------------------
    norm_current = {
        "shifts": [],
        "hours": [],
        "weekend": [],
        "score": [],
    }

    norm_total = {
        "shifts": [],
        "hours": [],
        "weekend": [],
        "score": [],
    }

    # -------------------------
    # Compute normalized stats
    # -------------------------
    for i in employees:
        denom = max(availability[i], min_avail_floor)

        shifts_i = sum(works[i, j].X for j in events)
        hours_i = sum(works[i, j].X * shift_dur[j] for j in events)
        weekend_i = sum(works[i, j].X * is_weekend[j] for j in events)
        score_i = sum(
            works[i, j].X * dict_events[j]["EventRanking"]
            for j in events
        )

        # CURRENT (normalized)
        norm_current["shifts"].append(shifts_i / denom)
        norm_current["hours"].append(hours_i / denom)
        norm_current["weekend"].append(weekend_i / denom)
        norm_current["score"].append(score_i / denom)

        # TOTAL = history + current (normalized)
        norm_total["shifts"].append((shifts_i + hist_shifts.get(i, 0)) / denom)
        norm_total["hours"].append((hours_i + hist_hours.get(i, 0)) / denom)
        norm_total["weekend"].append((weekend_i + hist_weekend.get(i, 0)) / denom)
        norm_total["score"].append((score_i + hist_scores.get(i, 0)) / denom)

    # -------------------------
    # PRINT NORMALIZED STATS
    # -------------------------
    print("\n--- Current Period (NORMALIZED) ---")
    for key, values in norm_current.items():
        v = np.array(values, dtype=float)
        print(f"\n{key}:")
        print("  Min:", round(v.min(), 2))
        print("  Max:", round(v.max(), 2))
        print("  Avg:", round(v.mean(), 2))
        print("  Std:", round(v.std(), 2))

    print("\n--- Total (History + Current) (NORMALIZED) ---")
    for key, values in norm_total.items():
        v = np.array(values, dtype=float)
        print(f"\n{key}:")
        print("  Min:", round(v.min(), 2))
        print("  Max:", round(v.max(), 2))
        print("  Avg:", round(v.mean(), 2))
        print("  Std:", round(v.std(), 2))
