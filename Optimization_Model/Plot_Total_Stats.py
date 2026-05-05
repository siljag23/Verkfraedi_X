import matplotlib.pyplot as plt

def Plot_Total_Stats(raw_current, raw_total):

    ids = list(range(1, max(raw_total.keys()) + 1))

    # -------------------------
    # Extract
    # -------------------------
    def get_vals(key):
        curr = [raw_current.get(i, {}).get(key, 0) for i in ids]
        total = [raw_total.get(i, {}).get(key, 0) for i in ids]
        hist = [t - c for t, c in zip(total, curr)]
        return hist, curr

    # -------------------------
    # Generic plot
    # -------------------------
    def plot_metric(hist, curr, title, ylabel):

        plt.figure(figsize=(12,6))

        plt.bar(ids, hist, color="black", label="Last period")
        plt.bar(ids, curr, bottom=hist, color="#ff6e1b", label="Current period")

        plt.title(title, fontweight="bold")
        plt.xlabel("Employee ID")
        plt.ylabel(ylabel)

        plt.xticks(ids)
        plt.legend()
        plt.tight_layout()
        plt.show()

    # -------------------------
    # Plots
    # -------------------------
    hist, curr = get_vals("shifts")
    plot_metric(hist, curr, "Total Shifts", "Shifts")

    hist, curr = get_vals("hours")
    plot_metric(hist, curr, "Total Hours", "Hours")

    hist, curr = get_vals("score")
    plot_metric(hist, curr, "Total Score", "Score")

    hist, curr = get_vals("weekend")
    plot_metric(hist, curr, "Total Weekend Shifts", "Weekend Shifts")