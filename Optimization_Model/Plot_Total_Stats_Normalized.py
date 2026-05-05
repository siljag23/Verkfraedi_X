import matplotlib.pyplot as plt

def Plot_Total_Stats_Normalized(norm_current, norm_history):

    ids = list(range(1, max(norm_current.keys()) + 1))

    color_hist = "black"
    color_curr = "#ff6e1b"
    label_hist = "Last period"
    label_curr = "Current period"

    # -------------------------
    # SHIFTS
    # -------------------------
    hist_shifts = [round(norm_history.get(i, {}).get("shifts", 0)) for i in ids]
    curr_shifts = [round(norm_current.get(i, {}).get("shifts", 0)) for i in ids]
    plt.figure(figsize=(12,6))

    plt.bar(ids, hist_shifts, color=color_hist, label=label_hist)
    plt.bar(ids, curr_shifts, bottom=hist_shifts, color=color_curr, label=label_curr)

    plt.title("Total Shifts (Normalized)", fontweight="bold", fontsize = 20)
    plt.xlabel("Employee ID", fontweight="bold", fontsize = 15)
    plt.ylabel("Shifts", fontweight="bold", fontsize = 15)
    plt.legend()
    
    plt.xticks(ids)
    plt.tight_layout()
    plt.show()

    # -------------------------
    # HOURS
    # -------------------------
    hist_hours = [round(norm_history.get(i, {}).get("hours", 0)*2)/2 for i in ids]
    curr_hours = [round(norm_current.get(i, {}).get("hours", 0)*2)/2 for i in ids]
    plt.figure(figsize=(12,6))

    plt.bar(ids, hist_hours, color=color_hist, label=label_hist)
    plt.bar(ids, curr_hours, bottom=hist_hours, color=color_curr, label=label_curr)

    plt.title("Total Hours (Normalized)", fontweight="bold", fontsize = 20)
    plt.xlabel("Employee ID", fontweight="bold", fontsize = 15)
    plt.ylabel("Hours", fontweight="bold", fontsize = 15)

    plt.xticks(ids)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # -------------------------
    # WEEKEND SHIFTS
    # -------------------------
    hist_weekend = [round(norm_history.get(i, {}).get("weekend", 0)) for i in ids]
    curr_weekend = [round(norm_current.get(i, {}).get("weekend", 0)) for i in ids]

    plt.figure(figsize=(12,6))

    plt.bar(ids, hist_weekend, color=color_hist, label=label_hist)
    plt.bar(ids, curr_weekend, bottom=hist_weekend, color=color_curr, label=label_curr)

    plt.title("Total Weekend Shifts (Normalized)", fontweight="bold", fontsize = 20)
    plt.xlabel("Employee ID", fontweight="bold", fontsize = 15)
    plt.ylabel("Weekend Shifts", fontweight="bold", fontsize = 15)

    plt.xticks(ids)
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    # -------------------------
    # SCORE
    # -------------------------
    hist_score = [round(norm_history.get(i, {}).get("score", 0)) for i in ids]
    curr_score = [round(norm_current.get(i, {}).get("score", 0)) for i in ids]

    plt.figure(figsize=(12,6))

    plt.bar(ids, hist_score, color=color_hist, label=label_hist)
    plt.bar(ids, curr_score, bottom=hist_score, color=color_curr, label=label_curr)

    plt.title("Total Score (Normalized)", fontweight="bold", fontsize = 20)
    plt.xlabel("Employee ID", fontweight="bold", fontsize = 15)
    plt.ylabel("Score", fontweight="bold", fontsize = 15)

    plt.xticks(ids)
    plt.legend()
    plt.tight_layout()
    plt.show()
