import numpy as np
from Optimization_Staff_Scheduling2 import Optimization_Staff_Scheduling2

def Total_Stats(
    employees,
    events,
    dict_events,
    dict_employees,
    employee_days,
    hist_shifts=None,
    hist_hours=None,
    hist_scores=None,
    hist_weekend=None,
    requests=None,
    NUM_RUNS=50
):

    hist_shifts = hist_shifts or {}
    hist_hours = hist_hours or {}
    hist_scores = hist_scores or {}
    hist_weekend = hist_weekend or {}

    all_current = {"shifts": [], "hours": [], "weekend": [], "score": [], "normalized_hours": []}
    all_total = {"shifts": [], "hours": [], "weekend": [], "score": [], "normalized_hours": []}

    print("\nRunning multiple runs for stats...")

    for run in range(NUM_RUNS):

        model, works, shift_dur, weekend, weeks, event_date = Optimization_Staff_Scheduling2(
            dict_events,
            dict_employees,
            employee_days,
            hist_shifts,
            hist_hours,
            hist_halls=None,
            hist_weekend=hist_weekend,
            requests=requests
        )

        if model.SolCount == 0:
            continue

        # -------------------------
        # Availability
        # -------------------------
        total_days = len(set(event_date[j].date() for j in events))
        availability = {}

        for i in employees:
            days_off = employee_days.get(i, set())
            availability[i] = (total_days - len(days_off)) / total_days if total_days > 0 else 1

        # -------------------------
        # Compute per run
        # -------------------------
        current = {"shifts": [], "hours": [], "weekend": [], "score": [], "normalized_hours": []}
        total = {"shifts": [], "hours": [], "weekend": [], "score": [], "normalized_hours": []}

        for i in employees:

            shifts_i = sum(works[i,j].X for j in events)
            hours_i = sum(works[i,j].X * shift_dur[j] for j in events)
            weekend_i = sum(
                works[i,j].X for j in events
                if event_date[j].weekday() in [4,5,6]
            )
            score_i = sum(works[i,j].X * dict_events[j]["EventRanking"] for j in events)

            avail = availability[i]

            # CURRENT
            current["shifts"].append(shifts_i)
            current["hours"].append(hours_i)
            current["weekend"].append(weekend_i)
            current["score"].append(score_i)
            current["normalized_hours"].append(hours_i / max(avail, 0.1))

            # TOTAL
            total_hours = hours_i + hist_hours.get(i, 0)
            total_shifts = shifts_i + hist_shifts.get(i, 0)
            total_weekend = weekend_i + hist_weekend.get(i, 0)
            total_score = score_i + hist_scores.get(i, 0)

            total["shifts"].append(total_shifts)
            total["hours"].append(total_hours)
            total["weekend"].append(total_weekend)
            total["score"].append(total_score)
            total["normalized_hours"].append(total_hours / max(avail, 0.1))

        # -------------------------
        # Save results
        # -------------------------
        for key in all_current:
            all_current[key].extend(current[key])
            all_total[key].extend(total[key])

    # -------------------------
    # PRINT
    # -------------------------
    def print_stats(title, stats):
        print(f"\n--- {title} ---")

        for key, values in stats.items():
            print(f"\n{key}:")
            print("  Min:", round(np.min(values), 2))
            print("  Max:", round(np.max(values), 2))
            print("  Avg:", round(np.mean(values), 2))
            print("  Std:", round(np.std(values), 2))

    print_stats("Current Period (AVERAGED)", all_current)
    print_stats("Total (History + Current) (AVERAGED)", all_total)

    return all_current, all_total