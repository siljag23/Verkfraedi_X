import matplotlib.pyplot as plt

def Plot_Total_Stats(
    raw_current,
    raw_total,
    norm_current,
    norm_total,
    dict_employees
):

    COLOR_HIST = "black"
    COLOR_CURR = "#ff6e1b"

    # -------------------------
    # Build stacked data (with rounding for normalized)
    # -------------------------
    def build_stacked_metric(cur_data, tot_data, key, normalized=False):

        data = []

        for i in tot_data:

            label = str(i)

            total_val = tot_data[i][key]
            current_val = cur_data[i][key]

            # -------------------------
            # ROUND ONLY FOR NORMALIZED PLOTS
            # -------------------------
            if normalized:
                if key in ["shifts", "weekend"]:
                    total_val = round(total_val)
                    current_val = round(current_val)

                elif key == "hours":
                    total_val = round(total_val * 2) / 2
                    current_val = round(current_val * 2) / 2

                elif key == "score":
                    total_val = round(total_val)
                    current_val = round(current_val)

            # -------------------------
            # STACK
            # -------------------------
            hist = total_val - current_val
            curr = current_val

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
    # RAW plots
    # -------------------------
    plot_stacked(
        sort_data(build_stacked_metric(raw_current, raw_total, "shifts")),
        "Total Shifts",
        "Shifts"
    )

    plot_stacked(
        sort_data(build_stacked_metric(raw_current, raw_total, "hours")),
        "Total Hours",
        "Hours"
    )

    plot_stacked(
        sort_data(build_stacked_metric(raw_current, raw_total, "score")),
        "Total Score",
        "Score"
    )

    plot_stacked(
        sort_data(build_stacked_metric(raw_current, raw_total, "weekend")),
        "Total Shifts on Weekends",
        "Shifts"
    )

    # -------------------------
    # NORMALIZED plots (ROUNDED)
    # -------------------------
    plot_stacked(
        sort_data(build_stacked_metric(norm_current, norm_total, "shifts", normalized=True)),
        "Total Shifts (Normalized)",
        "Shifts"
    )

    plot_stacked(
        sort_data(build_stacked_metric(norm_current, norm_total, "hours", normalized=True)),
        "Total Hours (Normalized)",
        "Hours"
    )

    plot_stacked(
        sort_data(build_stacked_metric(norm_current, norm_total, "score", normalized=True)),
        "Total Score (Normalized)",
        "Score"
    )

    plot_stacked(
        sort_data(build_stacked_metric(norm_current, norm_total, "weekend", normalized=True)),
        "Total Shifts on Weekends (Normalized)",
        "Shifts"
    )