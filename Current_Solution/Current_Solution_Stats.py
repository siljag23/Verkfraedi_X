import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def Compute_Manual_Stats(excel_path, dict_events, shift_dur, sheet_name, employees):

    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    stats = {}

    for _, row in df.iterrows():

        event_id = int(float(row.iloc[0]))
        
        if isinstance(event_id, float):
            event_id = int(event_id)

        if event_id not in dict_events:
            continue

        event = dict_events[event_id]
        duration = shift_dur[event_id]
        score = event["EventRanking"]
        date = pd.to_datetime(event["Date"])
        is_weekend = date.weekday() in [4,5,6]

        for emp in row.iloc[1:]:

            if pd.isna(emp):
                continue

            emp = int(float(emp))

            if emp not in stats:
                stats[emp] = {
                    "shifts": 0,
                    "hours": 0,
                    "weekend": 0,
                    "score": 0
                }

            stats[emp]["shifts"] += 1
            stats[emp]["hours"] += duration
            stats[emp]["score"] += score

            if is_weekend:
                stats[emp]["weekend"] += 1

    for i in employees:
        if i not in stats:
            stats[i] = {
                "shifts": 0,
                "hours": 0,
                "weekend": 0,
                "score": 0
            }

    return stats

def Normalize_Manual_Stats(manual_stats, availability):

    norm_stats = {}

    for i in manual_stats:

        avail = availability.get(i, 0)

        if avail == 0:
            continue  

        s = manual_stats[i]

        norm_stats[i] = {
            "shifts": s["shifts"] / avail,
            "hours": s["hours"] / avail,
            "weekend": s["weekend"] / avail,
            "score": s["score"] / avail,
        }

    return norm_stats

def Combine_Stats(stats_1, stats_2):

    total = {}

    all_ids = set(stats_1.keys()) | set(stats_2.keys())

    for i in all_ids:

        s1 = stats_1.get(i, {})
        s2 = stats_2.get(i, {})

        total[i] = {
            "shifts": s1.get("shifts", 0) + s2.get("shifts", 0),
            "hours": s1.get("hours", 0) + s2.get("hours", 0),
            "weekend": s1.get("weekend", 0) + s2.get("weekend", 0),
            "score": s1.get("score", 0) + s2.get("score", 0),
        }

    return total

def Print_Manual_Stats(stats, title):

    print(f"\n--- {title} ---\n")

    for i in sorted(stats):

        s = stats[i]

        print(
            f"{i:2} | "
            f"Shifts: {s['shifts']:2} | "
            f"Hours: {s['hours']:5.1f} | "
            f"Weekend: {s['weekend']:2} | "
            f"Score: {s['score']:5.0f}"
        )

def Print_Summary(title, stats):

    print(f"\n--- {title} ---")

    metrics = ["shifts", "hours", "weekend", "score"]

    for key in metrics:

        values = [stats[i][key] for i in stats if key in stats[i]]

        if len(values) == 0:
            print(f"\n{key}: No data")
            continue

        v = np.array(values, dtype=float)

        print(f"\n{key}:")
        print("  Min:", round(v.min(), 2))
        print("  Max:", round(v.max(), 2))
        print("  Avg:", round(v.mean(), 2))
        print("  Std:", round(v.std(), 2))

def Round_Stats(stats):

    rounded = {}

    for i, s in stats.items():
        rounded[i] = {
            "shifts": round(s["shifts"]),
            "hours": round(s["hours"] * 2) / 2,
            "weekend": round(s["weekend"]),
            "score": round(s["score"]),
        }

    return rounded

def Plot_Manual_Total(manual_current, manual_history, title, normalized=False):

    ids = sorted(set(manual_current.keys()) | set(manual_history.keys()))

    color_hist = "black"
    color_curr = "#ff6e1b"

    suffix = " (Normalized)" if normalized else ""

    def plot_metric(key, ylabel, metric_name):

        hist_vals = [manual_history.get(i, {}).get(key, 0) for i in ids]
        curr_vals = [manual_current.get(i, {}).get(key, 0) for i in ids]

        plt.figure(figsize=(12,6))

        plt.bar(ids, hist_vals, color=color_hist, label="Last period")
        plt.bar(ids, curr_vals, bottom=hist_vals, color=color_curr, label="Current period")

        plt.title(f"{metric_name} {suffix}", fontweight="bold")
        plt.xlabel("Employee ID")
        plt.ylabel(ylabel, fontweight="bold")

        plt.xticks(ids)
        plt.legend()
        plt.tight_layout()
        plt.show()

    plot_metric("shifts", "Shifts", "Total Shifts")
    plot_metric("hours", "Work Hours", "Total Work Hours")
    plot_metric("score", "Score", "Total Score")
    plot_metric("weekend", "Weekend Shifts", "Total Weekend Shifts")

def Print_Per_Employee(stats, title):

    print(f"\n--- {title} ---\n")

    for i in sorted(stats):
        s = stats[i]

        print(
            f"Emp {i:2} | "
            f"Shifts: {s['shifts']:2} | "
            f"Hours: {s['hours']:5.1f} | "
            f"Score: {s['score']:5.0f}"
        )

# Plot Manual Solution Seperate
def Plot_Manual_One(stats, title, normalized=False):

    stats = Round_Stats(stats)
    ids = sorted(stats.keys())
    x = np.arange(len(ids))

    suffix = " (Normalized)" if normalized else ""

    def plot_metric(key, ylabel, metric_name):

        values = [stats[i].get(key, 0) for i in ids]

        plt.figure(figsize=(12,6))

        plt.bar(x, values, color="#ff6e1b")

        plt.title(f"{metric_name} in {title}{suffix}", fontweight="bold")
        plt.xlabel("Employee ID", fontweight="bold")
        plt.ylabel(ylabel, fontweight="bold")

        plt.xticks(x, ids)
        plt.tight_layout()
        plt.show()

    plot_metric("shifts", "Shifts", "Total Shifts")
    plot_metric("hours", "Work Hours", "Total Work Hours")
    plot_metric("score", "Score", "Total Score")
    plot_metric("weekend", "Weekend Shifts", "Total Weekend Shifts")

