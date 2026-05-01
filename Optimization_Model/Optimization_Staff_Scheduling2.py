import pandas as pd
import gurobipy as gp
import calendar
from gurobipy import GRB
from datetime import timedelta
from Optimization_Model.Compute_Shift_Duration import To_Hours, Compute_Shift_Duration


def Optimization_Staff_Scheduling2(
    dict_events,
    dict_employees,
    employee_days,
    hist_shifts=None,
    hist_hours=None,
    hist_halls=None,
    hist_weekend=None,
    requests=None
):

    employees = list(dict_employees.keys())
    events = list(dict_events.keys())

    hist_shifts = hist_shifts or {}
    hist_hours = hist_hours or {}
    hist_halls = hist_halls or {}
    hist_weekend = hist_weekend or {}
    requests = requests or set()

    # -------------------------
    # WEIGHTS
    # -------------------------
    W_SHIFTS = 5
    W_HOURS = 5
    W_SCORE = 0.5
    W_WEEKEND = 1.5
    W_HALLS = 0.5
    W_WEEKLY_BALANCE = 0.5

    REWARD_REQUEST = 3
    PENALTY_HISTORY = 1.5

    # -------------------------
    # DATA
    # -------------------------
    emp_demand = {j: dict_events[j]["Employees"] for j in events}
    skill1_req = {j: dict_events[j]["Skillset1"] for j in events}
    skill2_req = {j: dict_events[j]["Skillset2"] for j in events}
    shift_score = {j: dict_events[j]["EventRanking"] for j in events}
    hall = {j: dict_events[j]["Hall"] for j in events}

    start = {j: dict_events[j]["ShiftBegins"] for j in events}
    event_date = {j: pd.to_datetime(dict_events[j]["Date"], dayfirst=True) for j in events}
    skill = {i: dict_employees[i]["Skillset"] for i in employees}

    weekend = {j: 1 if event_date[j].weekday() in [4,5,6] else 0 for j in events}
    weeks = sorted(set(event_date[j].isocalendar().week for j in events))
    halls = list(set(hall.values()))

    shift_dur = Compute_Shift_Duration(dict_events)

    # -------------------------
    # REST CONSTRAINTS
    # -------------------------
    shift_start = {}
    shift_end = {}

    for j in events:
        start_h = To_Hours(start[j])
        shift_start[j] = event_date[j] + pd.to_timedelta(start_h, unit="h")
        shift_end[j] = shift_start[j] + pd.to_timedelta(shift_dur[j], unit="h")

    blocked_pairs = set()
    sorted_events = sorted(events, key=lambda j: shift_start[j])

    for idx, j1 in enumerate(sorted_events):
        for j2 in sorted_events[idx+1:]:
            if shift_start[j2] - shift_end[j1] < timedelta(hours=11):
                blocked_pairs.add((j1, j2))
            else:
                break

    # -------------------------
    # AVAILABILITY
    # -------------------------
    any_date = next(iter(event_date.values()))
    year, month = any_date.year, any_date.month
    total_days = calendar.monthrange(year, month)[1]

    availability = {}
    for i in employees:
        days_off = {
            pd.to_datetime(d).date()
            for d in employee_days.get(i, set())
            if pd.to_datetime(d).month == month and pd.to_datetime(d).year == year
        }
        availability[i] = max(0, (total_days - len(days_off)) / total_days)

    # -------------------------
    # MODEL
    # -------------------------
    model = gp.Model("Event_staffing")

    works = model.addVars(employees, events, vtype=GRB.BINARY, name="works")
    works_hall = model.addVars(employees, halls, vtype=GRB.BINARY, name="works_hall")

    # -------------------------
    # CONSTRAINTS
    # -------------------------
    for j in events:
        model.addConstr(gp.quicksum(works[i,j] for i in employees) == emp_demand[j])

    for j in events:
        model.addConstr(gp.quicksum(works[i,j] for i in employees if skill[i] == 1) >= skill1_req[j])
        model.addConstr(gp.quicksum(works[i,j] for i in employees if skill[i] in [1,2]) >= skill2_req[j])

    for i in employees:
        for j in events:
            if event_date[j].date() in employee_days.get(i, set()):
                model.addConstr(works[i,j] == 0)

    for i in employees:
        for d in set(event_date[j].date() for j in events):
            model.addConstr(
                gp.quicksum(works[i,j] for j in events if event_date[j].date() == d) <= 1
            )

    model.addConstrs(
        (works[i,j1] + works[i,j2] <= 1
        for i in employees
        for (j1,j2) in blocked_pairs)
    )

    # weekly limits
    for i in employees:
        for week in weeks:
            model.addConstr(
                gp.quicksum(works[i,j] for j in events if event_date[j].isocalendar().week == week)
                <= 6
            )
            model.addConstr(
                gp.quicksum(works[i,j]*shift_dur[j] for j in events if event_date[j].isocalendar().week == week)
                <= 48
            )

    # hall linking
    for i in employees:
        for j in events:
            model.addConstr(works[i,j] <= works_hall[i, hall[j]])

    # -------------------------
    # METRICS
    # -------------------------
    shifts = {i: gp.quicksum(works[i,j] for j in events) for i in employees}
    hours = {i: gp.quicksum(works[i,j]*shift_dur[j] for j in events) for i in employees}
    score = {i: gp.quicksum(works[i,j]*shift_score[j] for j in events) for i in employees}

    weekend_emp = {
        i: gp.quicksum(works[i,j] for j in events if weekend[j] == 1)
        for i in employees
    }

    y_i_h = {(i,h): gp.quicksum(works[i,j] for j in events if hall[j] == h)
             for i in employees for h in halls}

    weekly_shifts = {(i,w): gp.quicksum(
        works[i,j] for j in events if event_date[j].isocalendar().week == w)
        for i in employees for w in weeks}

    # -------------------------
    # AVERAGES
    # -------------------------
    n = len(employees)

    avg_shifts = gp.quicksum(shifts[i] for i in employees) / n
    avg_hours = gp.quicksum(hours[i] for i in employees) / n
    avg_score = gp.quicksum(score[i] for i in employees) / n
    avg_weekend = gp.quicksum(weekend_emp[i] for i in employees) / n

    avg_hall = {h: gp.quicksum(y_i_h[i,h] for i in employees)/n for h in halls}
    avg_weekly = {w: gp.quicksum(weekly_shifts[i,w] for i in employees)/n for w in weeks}

    # -------------------------
    # DEVIATIONS
    # -------------------------
    dev_shifts = model.addVars(employees)
    dev_hours = model.addVars(employees)
    dev_score = model.addVars(employees)
    dev_weekend = model.addVars(employees)
    dev_hall = model.addVars(employees, halls)
    dev_weekly = model.addVars(employees, weeks)

    for i in employees:

        model.addConstr(dev_shifts[i] >= shifts[i] - availability[i]*avg_shifts)
        model.addConstr(dev_shifts[i] >= availability[i]*avg_shifts - shifts[i])

        model.addConstr(dev_hours[i] >= hours[i] - availability[i]*avg_hours)
        model.addConstr(dev_hours[i] >= availability[i]*avg_hours - hours[i])

        model.addConstr(dev_score[i] >= score[i] - availability[i]*avg_score)
        model.addConstr(dev_score[i] >= availability[i]*avg_score - score[i])

        model.addConstr(dev_weekend[i] >= weekend_emp[i] - availability[i]*avg_weekend)
        model.addConstr(dev_weekend[i] >= availability[i]*avg_weekend - weekend_emp[i])

        for h in halls:
            model.addConstr(dev_hall[i,h] >= y_i_h[i,h] - availability[i]*avg_hall[h])
            model.addConstr(dev_hall[i,h] >= availability[i]*avg_hall[h] - y_i_h[i,h])

        for w in weeks:
            model.addConstr(dev_weekly[i,w] >= weekly_shifts[i,w] - availability[i]*avg_weekly[w])
            model.addConstr(dev_weekly[i,w] >= availability[i]*avg_weekly[w] - weekly_shifts[i,w])

    # -------------------------
    # OBJECTIVE
    # -------------------------
    model.setObjective(
        - W_SHIFTS * gp.quicksum(dev_shifts[i] for i in employees)
        - W_HOURS * gp.quicksum(dev_hours[i] for i in employees)
        - W_SCORE * gp.quicksum(dev_score[i] for i in employees)
        - W_WEEKEND * gp.quicksum(dev_weekend[i] for i in employees)
        - W_HALLS * gp.quicksum(dev_hall[i,h] for i in employees for h in halls)
        - W_WEEKLY_BALANCE * gp.quicksum(dev_weekly[i,w] for i in employees for w in weeks),
        GRB.MAXIMIZE
    )

    model.setParam('MIPGap', 0.01)
    model.optimize()

    return model, works, shift_dur, weekend, weeks, event_date