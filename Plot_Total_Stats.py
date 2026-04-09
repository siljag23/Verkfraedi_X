import matplotlib.pyplot as plt
import locale
import numpy as np


def Plot_Total_Stats(
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

    # =====================================================
    # AVAILABILITY (NEW)
    # =====================================================
    total_days = len(set(event_date[j].date() for j in events))

    availability = {}
    for i in employees:
        days_off = employee_days.get(i, set())
        availability[i] = (total_days - len(days_off)) / total_days if total_days > 0 else 1

    # =====================================================
    # BUILD DATA
    # =====================================================
    data = []

    for i in employees:

        name = dict_employees[i]["EmployeeName"]

        # CURRENT
        c_shifts = sum(works[i, j].X for j in events)
        c_hours = sum(works[i, j].X * shift_dur[j] for j in events)
        c_score = sum(works[i, j].X * shift_score[j] for j in events)
        c_weekend = sum(
            works[i, j].X
            for j in events
            if event_date[j].weekday() in [4, 5, 6]
        )

        # HISTORY
        h_shifts = hist_shifts.get(i, 0)
        h_hours = hist_hours.get(i, 0)
        h_score = hist_scores.get(i, 0)
        h_weekend = hist_weekend.get(i, 0)

        # =====================================================
        # NORMALIZED (NEW)
        # =====================================================
        total_hours = h_hours + c_hours
        norm_hours = total_hours / max(availability[i], 0.1)

        data.append({
            "name": name,
            "c_shifts": c_shifts,
            "h_shifts": h_shifts,
            "c_hours": c_hours,
            "h_hours": h_hours,
            "total_hours": total_hours,    
            "norm_hours": norm_hours,      
            "c_score": c_score,
            "h_score": h_score,
            "c_weekend": c_weekend,
            "h_weekend": h_weekend
        })

    # =====================================================
    # SORT (ICELANDIC FRIENDLY)
    # =====================================================
    try:
        locale.setlocale(locale.LC_ALL, 'is_IS.UTF-8')
        data = sorted(data, key=lambda x: locale.strxfrm(x["name"]))
    except:
        data = sorted(data, key=lambda x: x["name"])

    # =====================================================
    # UNPACK
    # =====================================================
    names = [d["name"] for d in data]

    current_shifts = [d["c_shifts"] for d in data]
    hist_shifts_vals = [d["h_shifts"] for d in data]

    current_hours = [d["c_hours"] for d in data]
    hist_hours_vals = [d["h_hours"] for d in data]

    current_scores = [d["c_score"] for d in data]
    hist_scores_vals = [d["h_score"] for d in data]

    current_weekend = [d["c_weekend"] for d in data]
    hist_weekend_vals = [d["h_weekend"] for d in data]

    # =====================================================
    # NORMALIZED UNPACK (NEW)
    # =====================================================
    total_hours_vals = [d["total_hours"] for d in data]
    norm_hours_vals = [d["norm_hours"] for d in data]

    COLOR_HIST = "black"
    COLOR_NEW = "#ff6e1b"

    # =====================================================
    # SHIFTS
    # =====================================================
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_shifts_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, current_shifts, bottom=hist_shifts_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Shifts", fontweight="bold")
    plt.ylabel("Number of Shifts", fontweight="bold")
    plt.xticks(rotation=90)
    plt.ylim(0, 10)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # =====================================================
    # HOURS
    # =====================================================
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_hours_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, current_hours, bottom=hist_hours_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total work hours", fontweight="bold")
    plt.ylabel("Hours", fontweight="bold")
    plt.xticks(rotation=90)
    plt.ylim(0, 35)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # =====================================================
    # SCORE
    # =====================================================
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_scores_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, current_scores, bottom=hist_scores_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total score", fontweight="bold")
    plt.ylabel("Score", fontweight="bold")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # =====================================================
    # WEEKEND
    # =====================================================
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_weekend_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, current_weekend, bottom=hist_weekend_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Shifts on Weekends", fontweight="bold")
    plt.ylabel("Number of Shifts on Weekends", fontweight="bold")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # =====================================================
    # NORMALIZED WORK HOURS
    # =====================================================
    plt.figure(figsize=(12,6))
    plt.bar(names, norm_hours_vals, color="#ff6e1b")
    plt.title("Normalized Work Hours", fontweight="bold")
    plt.ylabel("Work Hours / Availability", fontweight="bold")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

    # =====================================================
    # PRINT STATS 📊
    # =====================================================
    print("\n================ TOTAL STATS =================\n")

    def print_stats(label, values):
        print(f"{label}:")
        print(f"  Avg: {np.mean(values):.2f}")
        print(f"  Min: {np.min(values):.2f}")
        print(f"  Max: {np.max(values):.2f}")
        print(f"  Std: {np.std(values):.2f}\n")

    print_stats("Total Shifts", [h + c for h, c in zip(hist_shifts_vals, current_shifts)])
    print_stats("Total Hours", total_hours_vals)
    print_stats("Normalized Hours", norm_hours_vals)
    print_stats("Total Score", [h + c for h, c in zip(hist_scores_vals, current_scores)])
    print_stats("Weekend Shifts", [h + c for h, c in zip(hist_weekend_vals, current_weekend)])
