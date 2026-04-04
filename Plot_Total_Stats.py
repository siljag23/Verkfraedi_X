import matplotlib.pyplot as plt
import locale


def Plot_Total_Stats(
    employees,
    events,
    works,
    dict_employees,
    shift_dur,
    shift_score,
    event_date,
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

        data.append({
            "name": name,
            "c_shifts": c_shifts,
            "h_shifts": h_shifts,
            "c_hours": c_hours,
            "h_hours": h_hours,
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

    COLOR_HIST = "black"
    COLOR_NEW = "#ff6e1b"

    # =====================================================
    # SHIFTS
    # =====================================================
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_shifts_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, current_shifts, bottom=hist_shifts_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Shifts")
    plt.ylabel("Number of Shifts")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # =====================================================
    # HOURS
    # =====================================================
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_hours_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, current_hours, bottom=hist_hours_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total work hours")
    plt.ylabel("Hours")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # =====================================================
    # SCORE
    # =====================================================
    plt.figure(figsize=(12,6))
    plt.bar(names, hist_scores_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, current_scores, bottom=hist_scores_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total score")
    plt.ylabel("Score")
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
    plt.title("Total Shifts on Weekends")
    plt.ylabel("Number of Shifts on Weekends")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()