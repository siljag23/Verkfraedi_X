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

    # -------------------------
    # BUILD DATA
    # -------------------------
    data = []

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

        data.append({
            "name": name,
            "c_shifts": s,
            "h_shifts": hs,
            "c_hours": h,
            "h_hours": hh,
            "c_score": sc,
            "h_score": hsc,
            "c_weekend": w,
            "h_weekend": hw
        })

    # -------------------------
    # SORT (ICELANDIC)
    # -------------------------
    try:
        locale.setlocale(locale.LC_ALL, 'is_IS.UTF-8')
        data = sorted(data, key=lambda x: locale.strxfrm(x["name"]))
    except:
        data = sorted(data, key=lambda x: x["name"])

    # -------------------------
    # UNPACK
    # -------------------------
    names = [d["name"] for d in data]

    c_shifts = [d["c_shifts"] for d in data]
    h_shifts_vals = [d["h_shifts"] for d in data]

    c_hours = [d["c_hours"] for d in data]
    h_hours_vals = [d["h_hours"] for d in data]

    c_scores = [d["c_score"] for d in data]
    h_scores_vals = [d["h_score"] for d in data]

    c_weekend = [d["c_weekend"] for d in data]
    h_weekend_vals = [d["h_weekend"] for d in data]

    COLOR_HIST = "black"
    COLOR_NEW = "#ff6e1b"

    # -------------------------
    # SHIFTS
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, h_shifts_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, c_shifts, bottom=h_shifts_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Shifts", fontweight="bold")
    plt.ylabel("Number of Shifts")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # -------------------------
    # HOURS
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, h_hours_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, c_hours, bottom=h_hours_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Work Hours", fontweight="bold")
    plt.ylabel("Hours")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # -------------------------
    # SCORE
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, h_scores_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, c_scores, bottom=h_scores_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Score", fontweight="bold")
    plt.ylabel("Score")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # -------------------------
    # WEEKEND
    # -------------------------
    plt.figure(figsize=(12,6))
    plt.bar(names, h_weekend_vals, color=COLOR_HIST, label="Last period")
    plt.bar(names, c_weekend, bottom=h_weekend_vals, color=COLOR_NEW, label="Current period")
    plt.title("Total Weekend Shifts", fontweight="bold")
    plt.ylabel("Number of Shifts")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()