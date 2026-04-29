import matplotlib.pyplot as plt

times = []
incumbent = []
bestbd = []
gap = []

with open("Optimization_Model/Gurobi.log", "r", encoding="utf-8") as f:
    for line in f:

        parts = line.split()
        if len(parts) < 10:
            continue

        try:
            t = float(parts[-1].replace("s", ""))
            g = float(parts[-3].replace("%", ""))
            bd = float(parts[-4])
            inc = float(parts[-5])
            if inc < 0:
                continue

            times.append(t)
            incumbent.append(inc)
            bestbd.append(bd)
            gap.append(g)

        except:
            continue


# -------------------------
# PLOT
# -------------------------
fig, ax1 = plt.subplots()

ax1.step(times, incumbent, where="post", label="Incumbent")
ax1.step(times, bestbd, where="post", linestyle="--", label="BestBd")
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Objective")

ax2 = ax1.twinx()
ax2.plot(times, gap, linestyle=":", label="Gap")
ax2.set_ylabel("Gap (%)")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2)

plt.title("Gurobi Progress")
plt.show()

# -------------------------
# ZOOMED PLOT
# -------------------------
fig, ax1 = plt.subplots()

ax1.step(times, incumbent, where="post", label="Incumbent")
ax1.step(times, bestbd, where="post", linestyle="--", label="BestBd")
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Objective")

ax2 = ax1.twinx()
ax2.step(times, gap, where="post", linestyle=":", label="Gap")
ax2.set_ylabel("Gap (%)")

ax1.set_xlim(0, 300)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2)

plt.title("Gurobi Progress (Zoomed)")
plt.show()