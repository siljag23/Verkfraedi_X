import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from open_excel import open_excel


# Opna excel
dict_events, dict_employees = open_excel("Input_opti.xlsx", "Events", "Employee")

# Model
model = gp.Model("Event_staffing")

# Indexar fyrir starfsmenn og viðburði
employees = list(dict_employees.keys())  
events = list(dict_events.keys())     


# Fastar
emp_demand = {j: dict_events[j]["Employees"] for j in events}

skill1_req = {j: dict_events[j]["Skillset1"] for j in events}
skill2_req = {j: dict_events[j]["Skillset2"] for j in events}

shift_score = {j: dict_events[j]["EventRanking"] for j in events}
hall = {j: dict_events[j]["Hall"] for j in events}

start = {j: dict_events[j]["ShiftBegins"] for j in events}
end = {j: dict_events[j]["ShiftsEnds"] for j in events}

event_date = {j: pd.to_datetime(dict_events[j]["Date"], dayfirst=True) for j in events}

skill = {i: dict_employees[i]["Skillset"] for i in employees}

weekend = {j: 1 if event_date[j].weekday() in [4,5] else 0 for j in events}


# Reikna duration fasta
shift_dur = {}

for j in events:

    start_hours = start[j].hour + start[j].minute/60
    end_hours = end[j].hour + end[j].minute/60

    if end_hours < start_hours:
        end_hours += 24

    shift_dur[j] = end_hours - start_hours


# Ákvörðunarbreyta
works = model.addVars(employees, events, vtype=GRB.BINARY, name="works")


# Breytur fyrir jafna dreifingu
min_score = model.addVar(name="min_score")
max_score = model.addVar(name="max_score")

min_shifts = model.addVar(name="min_shifts")
max_shifts = model.addVar(name="max_shifts")

min_workhours = model.addVar(name="min_workhours")
max_workhours = model.addVar(name="max_workhours")

min_weekend = model.addVar(name="min_weekend")
max_weekend = model.addVar(name="max_weekend")

max_halls = model.addVar(name="max_halls")


# Skorður
# Starfsmannaþörf
for j in events:

    model.addConstr(
        gp.quicksum(works[i,j] for i in employees) == emp_demand[j]
    )


# Skill 1 þörf
for j in events:

    model.addConstr(
        gp.quicksum(
            works[i,j]
            for i in employees
            if skill[i] == 1
        )
        >= skill1_req[j]
    )


# Skill 2 þörf
for j in events:

    model.addConstr(
        gp.quicksum(
            works[i,j]
            for i in employees
            if skill[i] in [1,2]
        )
        >= skill2_req[j]
    )


# Ekki hægt að vinna á tveimur vöktum í einu
for i in employees:
    for j1 in events:
        for j2 in events:

            if j1 < j2:

                if event_date[j1] == event_date[j2]:

                    if start[j1] < end[j2] and start[j2] < end[j1]:

                        model.addConstr(
                            works[i,j1] + works[i,j2] <= 1
                        )


# Jafna stig
for i in employees:

    model.addConstr(
        gp.quicksum(works[i,j] * shift_score[j] for j in events) >= min_score
    )

    model.addConstr(
        gp.quicksum(works[i,j] * shift_score[j] for j in events) <= max_score
    )


# Jafna fjölda vakta
for i in employees:

    model.addConstr(
        gp.quicksum(works[i,j] for j in events) >= min_shifts
    )

    model.addConstr(
        gp.quicksum(works[i,j] for j in events) <= max_shifts
    )


# Jafna fjölda sala
halls = list(set(hall[j] for j in events))

for i in employees:
    for h in halls:

        model.addConstr(
            gp.quicksum(
                works[i,j]
                for j in events
                if hall[j] == h
            )
            <= max_halls
        )


# Jafna vinnutíma
for i in employees:

    model.addConstr(
        gp.quicksum(works[i,j] * shift_dur[j] for j in events) >= min_workhours
    )

    model.addConstr(
        gp.quicksum(works[i,j] * shift_dur[j] for j in events) <= max_workhours
    )


# Jafna helgarvaktir
for i in employees:

    model.addConstr(
        gp.quicksum(works[i,j] * weekend[j] for j in events) >= min_weekend
    )

    model.addConstr(
        gp.quicksum(works[i,j] * weekend[j] for j in events) <= max_weekend
    )


# Markfall
a=b=c=d=e=f=g=h=i=1

model.setObjective(
    a*min_score - b*max_score
    + c*min_shifts - d*max_shifts
    + e*min_workhours - f*max_workhours
    - g*max_halls
    + h*min_weekend - i*max_weekend,
    GRB.MAXIMIZE
)


# Leysa
model.optimize()


# Prenta lausn
if model.status == GRB.OPTIMAL:

    print("\nSchedule:\n")

    sorted_events = sorted(events, key=lambda j: dict_events[j]["Event"])

    for j in sorted_events:

        workers = []

        for i in employees:
            if works[i,j].X > 0.5:
                workers.append(dict_employees[i]["EmployeeName"])

        workers.sort()

        event_name = dict_events[j]["Event"]
        event_date_print = dict_events[j]["Date"]
        start_time = dict_events[j]["ShiftBegins"]
        end_time = dict_events[j]["ShiftsEnds"]

        print(f"{event_name} | {event_date_print} | {start_time}-{end_time}")

        for w in workers:
            print("   ", w)

        print()

else:
    print("No feasible solution found")


# Ef líkanið er infeasible
if model.status == GRB.INFEASIBLE:

    print("Model infeasible, computing IIS...")

    model.computeIIS()

    model.write("infeasible_model.ilp")