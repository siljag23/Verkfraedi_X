import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from open_excel import open_excel
from datetime import timedelta


# Opna excel
dict_events, dict_employees, employee_days = open_excel("Input.xlsx","Events","Employees","DaysOff")

# Indexar
employees = list(dict_employees.keys())
events = list(dict_events.keys())

# Fastar
# Fastar fyrir reglur í kjarasamningum, 48 klst, 1 frídagur, 11 max vinna
emp_demand = {j: dict_events[j]["Employees"] for j in events}
skill1_req = {j: dict_events[j]["Skillset1"] for j in events}
skill2_req = {j: dict_events[j]["Skillset2"] for j in events}
shift_score = {j: dict_events[j]["EventRanking"] for j in events}
hall = {j: dict_events[j]["Hall"] for j in events}
start = {j: dict_events[j]["ShiftBegins"] for j in events}
end = {j: dict_events[j]["ShiftEnds"] for j in events}
event_date = {j: pd.to_datetime(dict_events[j]["Date"],dayfirst=True) for j in events}
skill = {i: dict_employees[i]["Skillset"] for i in employees}
weekend = {j: 1 if event_date[j].weekday() in [4,5] else 0 for j in events}

# duration vakta
shift_dur = {}

for j in events:

    if hasattr(start[j], "hour"):
        start_hours = start[j].hour + start[j].minute/60
    else:
        start_hours = start[j].total_seconds()/3600

    if hasattr(end[j], "hour"):
        end_hours = end[j].hour + end[j].minute/60
    else:
        end_hours = end[j].total_seconds()/3600

    if end_hours < start_hours:
        end_hours += 24

    shift_dur[j] = end_hours - start_hours


# overlap listi
# Koma með öll pör af vöktum sem má ekki vinna báðar
# Setja frí hér 
# Óskir 
overlap_pairs = []

for j1 in events:
    for j2 in events:

        if j1 < j2:

            if event_date[j1] == event_date[j2]:

                if start[j1] < end[j2] and start[j2] < end[j1]:
                    overlap_pairs.append((j1,j2))


# 13 klst hvíld listi
rest_pairs = []

for j1 in events:
    for j2 in events:

        if j1 != j2:

            end1 = event_date[j1] + pd.to_timedelta(start[j1].hour,unit="h")
            end1 += pd.to_timedelta(start[j1].minute,unit="m")
            end1 += pd.to_timedelta(shift_dur[j1],unit="h")

            start2 = event_date[j2] + pd.to_timedelta(start[j2].hour,unit="h")
            start2 += pd.to_timedelta(start[j2].minute,unit="m")

            if start2 > end1 and (start2 - end1) < timedelta(hours=13):
                rest_pairs.append((j1,j2))


# Model
model = gp.Model("Event_staffing")

# Ákvörðunarbreyta
works = model.addVars(employees,events,vtype=GRB.BINARY,name="works")

# Ekki vinna á frídögum
for i in employees:
    for j in events:

        if event_date[j].date() in employee_days.get(i, set()):

            model.addConstr(
                works[i,j] == 0
            )

# fairness breytur
min_score = model.addVar()
max_score = model.addVar()

min_shifts = model.addVar()
max_shifts = model.addVar()

min_workhours = model.addVar()
max_workhours = model.addVar()

min_weekend = model.addVar()
max_weekend = model.addVar()

max_halls = model.addVar()

min_weekly_shifts = model.addVar()
max_weekly_shifts = model.addVar()


# Starfsmannaþörf
for j in events:
    model.addConstr(
        gp.quicksum(works[i,j] for i in employees)
        == emp_demand[j]
    )


# Skill skorður
for j in events:

    model.addConstr(
        gp.quicksum(
            works[i,j]
            for i in employees
            if skill[i] == 1
        ) >= skill1_req[j]
    )

    model.addConstr(
        gp.quicksum(
            works[i,j]
            for i in employees
            if skill[i] in [1,2]
        ) >= skill2_req[j]
    )


# overlap
for i in employees:
    for j1,j2 in overlap_pairs:

        model.addConstr(
            works[i,j1] + works[i,j2] <= 1
        )


# 13 klst hvíld
for i in employees:
    for j1,j2 in rest_pairs:

        model.addConstr(
            works[i,j1] + works[i,j2] <= 1
        )


# max 1 vakt á dag, overlap á að vera fyrir dag ekki sama tíma
days = sorted(set(event_date[j].date() for j in events))

for i in employees:
    for d in days:

        model.addConstr(
            gp.quicksum(
                works[i,j]
                for j in events
                if event_date[j].date()==d
            ) <= 1
        )


# max 11 klst á dag, taka út vaktir stjórna 
for i in employees:
    for d in days:

        model.addConstr(
            gp.quicksum(
                works[i,j]*shift_dur[j]
                for j in events
                if event_date[j].date()==d
            ) <= 11
        )


# min 3 vaktir
for i in employees:

    model.addConstr(
        gp.quicksum(works[i,j] for j in events) >= 3
    )


# amk einn frídagur á viku
weeks = sorted(set(event_date[j].isocalendar().week for j in events))

for i in employees:
    for w in weeks:

        model.addConstr(
            gp.quicksum(
                works[i,j]
                for j in events
                if event_date[j].isocalendar().week==w
            ) <= 6
        )


# fairness skorður
for i in employees:

    model.addConstr(
        gp.quicksum(works[i,j]*shift_score[j] for j in events)
        >= min_score
    )

    model.addConstr(
        gp.quicksum(works[i,j]*shift_score[j] for j in events)
        <= max_score
    )

    model.addConstr(
        gp.quicksum(works[i,j] for j in events)
        >= min_shifts
    )

    model.addConstr(
        gp.quicksum(works[i,j] for j in events)
        <= max_shifts
    )

    model.addConstr(
        gp.quicksum(works[i,j]*shift_dur[j] for j in events)
        >= min_workhours
    )

    model.addConstr(
        gp.quicksum(works[i,j]*shift_dur[j] for j in events)
        <= max_workhours
    )

    model.addConstr(
        gp.quicksum(works[i,j]*weekend[j] for j in events)
        >= min_weekend
    )

    model.addConstr(
        gp.quicksum(works[i,j]*weekend[j] for j in events)
        <= max_weekend
    )


# jafna vaktir milli vikna
for w in weeks:

    model.addConstr(
        gp.quicksum(
            works[i,j]
            for i in employees
            for j in events
            if event_date[j].isocalendar().week == w
        )
        >= min_weekly_shifts
    )

    model.addConstr(
        gp.quicksum(
            works[i,j]
            for i in employees
            for j in events
            if event_date[j].isocalendar().week == w
        )
        <= max_weekly_shifts
    )


# Markfall
# setja fasta efst
a = 90
b = 91
c = 100
d = 101
e = 90
f = 91
g = 30
h = 50
i = 51
j = 70
k = 71

model.setObjective(
    a*min_score - b*max_score
    + c*min_shifts - d*max_shifts
    + e*min_workhours - f*max_workhours
    - g*max_halls
    + h*min_weekend - i*max_weekend
    + j*min_weekly_shifts - k*max_weekly_shifts,
    GRB.MAXIMIZE
)


# Solver stillingar
model.setParam("MIPGap",0.05)
model.setParam("TimeLimit",180)

# Leysa
model.optimize()


# Prenta schedule
if model.status in [GRB.OPTIMAL,GRB.TIME_LIMIT]:

    print("\nSchedule:\n")

    sorted_events = sorted(events,key=lambda j:(event_date[j],start[j]))

    for j in sorted_events:

        workers = []

        for i in employees:
            if works[i,j].X > 0.5:
                workers.append(dict_employees[i]["EmployeeName"])

        workers = sorted(set(workers))

        if len(workers)>0:

            print(f"{dict_events[j]['Date']} | {start[j]}-{end[j]} | {dict_events[j]['Event']}")

            for w in workers:
                print("   ",w)

            print()


print("\n--- EMPLOYEE SUMMARY ---\n")

for i in employees:

    shifts = sum(works[i,j].X for j in events)
    hours = sum(works[i,j].X * shift_dur[j] for j in events)
    score = sum(works[i,j].X * shift_score[j] for j in events)
    weekend_shifts = sum(works[i,j].X * weekend[j] for j in events)

    name = dict_employees[i]["EmployeeName"]

    print(
        f"{name:10} | shifts: {shifts:2.0f} | hours: {hours:5.1f} | score: {score:4.0f} | weekend: {weekend_shifts:2.0f}"
    )

print("\n--- SHIFTS PER WEEK PER EMPLOYEE ---\n")

for i in employees:

    name = dict_employees[i]["EmployeeName"]

    print(name)

    for w in weeks:

        count = sum(
            works[i,j].X
            for j in events
            if event_date[j].isocalendar().week == w
        )

        if count > 0:
            print(f"   Week {w}: {int(count)} shifts")

    print()

# Vista í excel 
schedule_rows = []

for j in events:
    for i in employees:
        if works[i,j].X > 0.5:

            schedule_rows.append({
                "Date": event_date[j].date(),
                "Start": start[j],
                "End": end[j],
                "Event": dict_events[j]["Event"],
                "Employee": dict_employees[i]["EmployeeName"]
            })

schedule_df = pd.DataFrame(schedule_rows)
schedule_df = schedule_df.sort_values(["Date","Start","Event"])

event_groups = schedule_df.groupby(["Date","Start","Event"])["Employee"].apply(list)

event_table = {}

for (d,s,e), workers in event_groups.items():
    col_name = f"{e}\n{d} {s}"
    event_table[col_name] = workers

event_df = pd.DataFrame(dict([(k,pd.Series(v)) for k,v in event_table.items()]))

employee_groups = schedule_df.groupby("Employee")

employee_table = {}

for emp, rows in employee_groups:

    events_list = []

    for _,r in rows.iterrows():
        events_list.append(f"{r['Event']}\n{r['Date']} {r['Start']}")

    employee_table[emp] = events_list

employee_df = pd.DataFrame(dict([(k,pd.Series(v)) for k,v in employee_table.items()]))

schedule_df["Day"] = schedule_df["Date"]

calendar_groups = schedule_df.groupby(["Day","Event"])

calendar_rows = []

for (d,e),rows in calendar_groups:

    workers = ", ".join(rows["Employee"])

    calendar_rows.append({
        "Date": d,
        "Event": e,
        "Employees": workers
    })

calendar_df = pd.DataFrame(calendar_rows)
calendar_df = calendar_df.sort_values(["Date","Event"])

with pd.ExcelWriter("Schedule_results.xlsx") as writer:

    event_df.to_excel(writer, sheet_name="Staff_per_event", index=False)

    employee_df.to_excel(writer, sheet_name="Staff_per_employee", index=False)

    calendar_df.to_excel(writer, sheet_name="Calendar_overview", index=False)

print("Excel file created: Schedule_results.xlsx")
    
# Súlurit
"""
# Stig
import matplotlib.pyplot as plt

# safna nöfnum og stigum
names = []
scores = []

for i in employees:
    
    name = dict_employees[i]["EmployeeName"]
    
    score = sum(works[i,j].X * shift_score[j] for j in events)
    
    names.append(name)
    scores.append(score)

# raða eftir stigum (valfrjálst en snyrtilegra)
data = sorted(zip(names, scores), key=lambda x: x[1])
names, scores = zip(*data)

# teikna súlurit
plt.figure(figsize=(12,6))
plt.bar(names, scores)

plt.xlabel("Starfsmenn")
plt.ylabel("Fjöldi stiga")
plt.title("Dreifing stiga á starfsmenn")

plt.xticks(rotation=90)

plt.tight_layout()
plt.show()
"""

# Workhours
import matplotlib.pyplot as plt

names = []
hours = []

for i in employees:

    name = dict_employees[i]["EmployeeName"]

    workhours = sum(works[i,j].X * shift_dur[j] for j in events)

    names.append(name)
    hours.append(workhours)

# raða eftir vinnustundum (valfrjálst en snyrtilegra)
data = sorted(zip(names, hours), key=lambda x: x[1])
names, hours = zip(*data)

plt.figure(figsize=(12,6))
plt.bar(names, hours)

plt.xlabel("Starfsmenn")
plt.ylabel("Vinnustundir")
plt.title("Dreifing vinnustunda á starfsmenn")

plt.xticks(rotation=90)

plt.tight_layout()
plt.show()