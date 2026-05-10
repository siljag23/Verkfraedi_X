import matplotlib.pyplot as plt

times = []
incumbent = []
bestbd = []
gap = []

with open("Optimization_Model/Gurobi.log", "r", encoding="utf-8") as f:
    for line in f:

        if "s" not in line or "%" not in line:
            continue

        parts = line.split()
        try:
            t = float(parts[-1].replace("s", ""))
            g = float(parts[-3].replace("%", ""))
            bd = float(parts[-4])
            inc = float(parts[-5])

            times.append(t)
            incumbent.append(-inc)
            bestbd.append(-bd)
            gap.append(g)

        except:
            continue


# -------------------------
# PLOT
# -------------------------
fig, ax1 = plt.subplots(figsize=(14,6))

ax1.step(times, incumbent, where="post", label="Incumbent", color="black")
ax1.step(times, bestbd, where="post", linestyle="--", label="BestBd", color="#ff6e1b")
ax1.set_xlabel("Time (s)", fontsize=15, fontweight='bold')
ax1.set_ylabel("Objective", fontsize=15, fontweight='bold')
ax1.set_ylim(0, 400)

ax2 = ax1.twinx()
ax2.step(times, gap, where="post", linestyle=":", label="Gap", color="black")
ax2.set_ylabel("Gap [%]", fontsize=15, fontweight='bold')
ax2.set_ylim(0, 100)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2)

plt.title("Optimization Progress", fontsize = 20, fontweight='bold')
plt.show()

# -------------------------
# ZOOMED PLOT
# -------------------------
fig, ax1 = plt.subplots(figsize=(14,6))

ax1.step(times, incumbent, where="post", label="Incumbent", color="black")
ax1.step(times, bestbd, where="post", linestyle="--", label="BestBd", color="#ff6e1b")
ax1.set_xlabel("Time (s)", fontsize=15, fontweight='bold')
ax1.set_ylabel("Objective", fontsize=15, fontweight='bold')

ax2 = ax1.twinx()
ax2.step(times, gap, where="post", linestyle=":", label="Gap", color="black")
ax2.set_ylabel("Gap [%]", fontsize=15, fontweight='bold')

ax1.set_xlim(0, 1000)
ax2.set_ylim(20, 70)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2)

plt.title("Early Optimization Progress", fontsize = 20, fontweight='bold')
plt.show()