import numpy as np

def Total_Stats(
    employees,
    events,
    works,
    dict_employees,
    shift_dur,
    shift_score,
    event_date,
    employee_days,
    hist_shifts=None,
    hist_hours=None,
    hist_scores=None,
    hist_weekend=None
):

    
    hist_shifts = hist_shifts or {}
    hist_hours = hist_hours or {}
    hist_scores = hist_scores or {}
    hist_weekend = hist_weekend or {}

    # availability
    total_days = len(set(event_date[j].date() for j in events))
    availability = {}

    for i in employees:
        days_off = employee_days.get(i, set())
        availability[i] = (total_days - len(days_off)) / total_days if total_days > 0 else 1

    # containers
    total_shifts_vals = []
    total_hours_vals = []
    total_weekend_vals = []
    total_score_vals = []
    norm_hours_vals = []

    for i in employees:

        # current
        shifts_i = sum(works[i,j].X for j in events)
        hours_i = sum(works[i,j].X * shift_dur[j] for j in events)
        weekend_i = sum(
            works[i,j].X for j in events
            if event_date[j].weekday() in [4,5,6]
        )
        score_i = sum(works[i,j].X * shift_score[j] for j in events)

        # history
        total_shifts = shifts_i + hist_shifts.get(i, 0)
        total_hours = hours_i + hist_hours.get(i, 0)
        total_weekend = weekend_i + hist_weekend.get(i, 0)
        total_score = score_i + hist_scores.get(i, 0)

        # normalized
        avail = availability[i]
        norm_hours = total_hours / max(avail, 0.1)

        # append
        total_shifts_vals.append(total_shifts)
        total_hours_vals.append(total_hours)
        total_weekend_vals.append(total_weekend)
        total_score_vals.append(total_score)
        norm_hours_vals.append(norm_hours)

    # -------------------------
    # PRINT STATS
    # -------------------------
    def print_stats(name, values):
        print(f"\n{name}:")
        print("  Min:", round(np.min(values), 2))
        print("  Max:", round(np.max(values), 2))
        print("  Avg:", round(np.mean(values), 2))
        print("  Std:", round(np.std(values), 2))

    print("\n--- Summary Statistics ---")

    print_stats("Total shifts", total_shifts_vals)
    print_stats("Total hours", total_hours_vals)
    print_stats("Weekend shifts", total_weekend_vals)
    print_stats("Shift score", total_score_vals)
    print_stats("Normalized hours", norm_hours_vals)

    return {
        "shifts": total_shifts_vals,
        "hours": total_hours_vals,
        "weekend": total_weekend_vals,
        "score": total_score_vals,
        "normalized_hours": norm_hours_vals
    }