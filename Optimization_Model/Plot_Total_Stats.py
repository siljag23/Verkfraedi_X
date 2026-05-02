import matplotlib.pyplot as plt

def Plot_Total_Stats(
    raw_current,
    raw_total,
    norm_current,
    norm_total,
    norm_history   # 🔥 nýtt input!
):

    COLOR_HIST = "black"
    COLOR_CURR = "#ff6e1b"

    # -------------------------
    # Build stacked data (NO subtraction bug)
    # -------------------------
    def build_stacked_metric(cur_data, hist_data, key):

        data = []
        all_ids = set(cur_data.keys()) | set(hist_data.keys())
        for i in all_ids:

            label = str(i)

            hist = hist_data.get(i, {}).get(key, 0)
            curr = cur_data.get(i, {}).get(key, 0)

            data.append({
                "name": label,
                "hist": hist,
                "curr": curr
            })

        return data

    # -------------------------
    # Sort
    # -------------------------
    def sort_data(data):
        return sorted(data, key=lambda x: int(x["name"]))

    # -------------------------
    # Plot function
    # -------------------------
    def plot_stacked(data, title, ylabel):

        names = [d["name"] for d in data]
        hist = [d["hist"] for d in data]
        curr = [d["curr"] for d in data]

        plt.figure(figsize=(12,6))
        plt.bar(names, hist, color=COLOR_HIST, label="Last period")
        plt.bar(names, curr, bottom=hist, color=COLOR_CURR, label="Current period")

        plt.title(title, fontweight="bold")
        plt.ylabel(ylabel)
        plt.xlabel("Employee ID")
        plt.xticks(rotation=0)
        plt.legend()
        plt.tight_layout()
        plt.show()

    # -------------------------
    # RAW plots (OK að subtracta)
    # -------------------------
    def build_raw(cur_data, tot_data, key):
        data = []
        for i in tot_data:
            total_val = tot_data[i][key]
            curr_val = cur_data[i][key]
            hist_val = total_val - curr_val

            data.append({
                "name": str(i),
                "hist": hist_val,
                "curr": curr_val
            })
        return data

    plot_stacked(
        sort_data(build_raw(raw_current, raw_total, "shifts")),
        "Total Shifts",
        "Shifts"
    )

    plot_stacked(
        sort_data(build_raw(raw_current, raw_total, "hours")),
        "Total Hours",
        "Hours"
    )

    plot_stacked(
        sort_data(build_raw(raw_current, raw_total, "score")),
        "Total Score",
        "Score"
    )

    plot_stacked(
        sort_data(build_raw(raw_current, raw_total, "weekend")),
        "Total Weekend Shifts",
        "Shifts"
    )

    # -------------------------
    # NORMALIZED plots (🔥 FIXED)
    # -------------------------
    plot_stacked(
        sort_data(build_stacked_metric(norm_current, norm_history, "shifts")),
        "Total Shifts (Normalized)",
        "Shifts"
    )

    plot_stacked(
        sort_data(build_stacked_metric(norm_current, norm_history, "hours")),
        "Total Hours (Normalized)",
        "Hours"
    )

    plot_stacked(
        sort_data(build_stacked_metric(norm_current, norm_history, "score")),
        "Total Score (Normalized)",
        "Score"
    )

    plot_stacked(
        sort_data(build_stacked_metric(norm_current, norm_history, "weekend")),
        "Total Weekend Shifts (Normalized)",
        "Shifts"
    )