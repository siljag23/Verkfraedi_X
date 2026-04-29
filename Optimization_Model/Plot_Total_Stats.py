import matplotlib.pyplot as plt

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

    names = []
    c_shifts = []
    h_shifts_vals = []
    c_hours = []
    h_hours_vals = []
    c_scores = []
    h_scores_vals = []
    c_weekend = []
    h_weekend_vals = []

    for i in employees:

        name = dict_employees[i]["EmployeeName"]

        # CURRENT
        s = sum(works[i, j].X for j in events)
        h = sum(works[i, j].X * shift_dur[j] for j in events)
        sc = sum(works[i, j].X * shift_score[j] for j in events)
        w = sum(
            works[i, j].X
            for j in events
            if event_date[j].weekday() in [4, 5, 6]
        )

        # HISTORY
        hs = hist_shifts.get(i, 0)
        hh = hist_hours.get(i, 0)
        hsc = hist_scores.get(i, 0)
        hw = hist_weekend.get(i, 0)

        names.append(name)

        c_shifts.append(s)
        h_shifts_vals.append(hs)

        c_hours.append(h)
        h_hours_vals.append(hh)

        c_scores.append(sc)
        h_scores_vals.append(hsc)

        c_weekend.append(w)
        h_weekend_vals.append(hw)

    COLOR_HIST = "black"
    COLOR_NEW = "#ff6e1b"

    # -------------------------
    # SHIFTS
    # -------------------------
    plt.figure()
    plt.bar(names, h_shifts_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, c_shifts, bottom=h_shifts_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Shifts")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # -------------------------
    # HOURS
    # -------------------------
    plt.figure()
    plt.bar(names, h_hours_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, c_hours, bottom=h_hours_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Work Hours")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # -------------------------
    # SCORE
    # -------------------------
    plt.figure()
    plt.bar(names, h_scores_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, c_scores, bottom=h_scores_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Score")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # -------------------------
    # WEEKEND
    # -------------------------
    plt.figure()
    plt.bar(names, h_weekend_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, c_weekend, bottom=h_weekend_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Weekend Shifts")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()