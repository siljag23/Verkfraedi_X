import pandas as pd
import gurobipy as gp
from gurobipy import GRB


def Optimization_Staff_Scheduling2(
    dict_events,
    dict_employees,
    employee_days,
    hist_shifts=None,
    hist_hours=None,
    hist_halls=None,
    current_schedule=None,
    requests=None
):

    # =========================================================
    # SETS / INDICES
    # =========================================================
    employees = list(dict_employees.keys())
    events = list(dict_events.keys())

    hist_shifts = hist_shifts or {}
    hist_hours = hist_hours or {}
    hist_halls = hist_halls or {}
    requests = requests or set()

    # =========================================================
    # CONSTANTS (ONLY FIXED NUMBERS)
    # =========================================================
    MAX_WORKHOURS_PER_WEEK = 48
    MAX_WORKDAYS_PER_WEEK = 6

    W_SHIFTS = 1
    W_HOURS = 1.25
    W_SCORE = 0.8
    W_WEEKEND = 0.6
    W_HALLS = 0.5
    W_WEEKLY_BALANCE = 0.7

    REWARD_REQUEST = 75
    PENALTY_HISTORY = 5
    PENALTY_CHANGE = 20

    # =========================================================
    # HELPER
    # =========================================================
    def to_hours(t):
        if hasattr(t, "total_seconds"):
            return t.total_seconds() / 3600
        elif hasattr(t, "hour"):
            return t.hour + t.minute / 60
        else:
            try:
                t = pd.to_datetime(t)
                return t.hour + t.minute / 60
            except:
                return 0

    # =========================================================
    # PARAMETERS (FROM DATA)
    # =========================================================
    emp_demand = {j: dict_events[j]["Employees"] for j in events}
    skill1_req = {j: dict_events[j]["Skillset1"] for j in events}
    skill2_req = {j: dict_events[j]["Skillset2"] for j in events}
    shift_score = {j: dict_events[j]["EventRanking"] for j in events}
    hall = {j: dict_events[j]["Hall"] for j in events}

    start = {j: dict_events[j]["ShiftBegins"] for j in events}
    end = {j: dict_events[j]["ShiftEnds"] for j in events}

    event_date = {j: pd.to_datetime(dict_events[j]["Date"], dayfirst=True) for j in events}
    skill = {i: dict_employees[i]["Skillset"] for i in employees}

    weekend = {j: 1 if event_date[j].weekday() in [4,5,6] else 0 for j in events}
    weeks = sorted(set(event_date[j].isocalendar().week for j in events))
    halls = list(set(hall.values()))

    # =========================================================
    # DERIVED DATA
    # =========================================================
    shift_dur = {}
    for j in events:
        start_h = to_hours(start[j])
        end_h = to_hours(end[j])

        if end_h < start_h:
            end_h += 24

        dur = end_h - start_h
        if dur > 10:
            dur = 4

        shift_dur[j] = dur

    total_days = len(set(event_date[j].date() for j in events))

    availability = {}
    for i in employees:
        days_off = employee_days.get(i, set())
        availability[i] = (total_days - len(days_off)) / total_days if total_days > 0 else 1

    # =========================================================
    # MODEL
    # =========================================================
    model = gp.Model("Event_staffing")

    # =========================================================
    # DECISION VARIABLES
    # =========================================================
    works = model.addVars(employees, events, vtype=GRB.BINARY, name="works")
    change = model.addVars(employees, events, vtype=GRB.BINARY, name="change")
    works_hall = model.addVars(employees, halls, vtype=GRB.BINARY, name="works_hall")

    # =========================================================
    # FAIRNESS VARIABLES
    # =========================================================
    min_shifts = model.addVar()
    max_shifts = model.addVar()

    min_hours = model.addVar()
    max_hours = model.addVar()

    min_score = model.addVar()
    max_score = model.addVar()

    min_weekend = model.addVar()
    max_weekend = model.addVar()

    min_halls = model.addVar()
    max_halls = model.addVar()

    min_weekly = model.addVar()
    max_weekly = model.addVar()

    # =========================================================
    # CONSTRAINTS
    # =========================================================

    # Demand
    for j in events:
        model.addConstr(gp.quicksum(works[i,j] for i in employees) == emp_demand[j])

    # Skills
    for j in events:
        model.addConstr(gp.quicksum(works[i,j] for i in employees if skill[i] == 1) >= skill1_req[j])
        model.addConstr(gp.quicksum(works[i,j] for i in employees if skill[i] in [1,2]) >= skill2_req[j])

    # Vacation
    for i in employees:
        for j in events:
            if event_date[j].date() in employee_days.get(i, set()):
                model.addConstr(works[i,j] == 0)

    # Minimum shifts
    for i in employees:
        model.addConstr(
            gp.quicksum(works[i,j] for j in events) >= availability[i] * 3
        )

    # Weekly constraints
    for i in employees:
        for week in weeks:

            weekly_shifts = gp.quicksum(
                works[i,j] for j in events
                if event_date[j].isocalendar().week == week
            )

            weekly_hours = gp.quicksum(
                works[i,j] * shift_dur[j] for j in events
                if event_date[j].isocalendar().week == week
            )

            model.addConstr(weekly_shifts <= MAX_WORKDAYS_PER_WEEK)
            model.addConstr(weekly_hours <= MAX_WORKHOURS_PER_WEEK)

            model.addConstr(weekly_shifts >= min_weekly)
            model.addConstr(weekly_shifts <= max_weekly)

    # Hall linking
    for i in employees:
        for j in events:
            model.addConstr(works[i,j] <= works_hall[i, hall[j]])

    # Hall fairness (with history)
    for i in employees:
        total_halls = gp.quicksum(works_hall[i,h] for h in halls) + sum(hist_halls.get(i, {}).values())
        model.addConstr(total_halls >= min_halls)
        model.addConstr(total_halls <= max_halls)

    # Change constraints
    if current_schedule is not None:
        for i in employees:
            for j in events:
                curr = current_schedule.get((i,j), 0)
                model.addConstr(change[i,j] >= works[i,j] - curr)
                model.addConstr(change[i,j] >= curr - works[i,j])

    # Fairness constraints
    for i in employees:

        shifts_i = gp.quicksum(works[i,j] for j in events)
        hours_i = gp.quicksum(works[i,j]*shift_dur[j] for j in events)
        score_i = gp.quicksum(works[i,j]*shift_score[j] for j in events)
        weekend_i = gp.quicksum(works[i,j]*weekend[j] for j in events)

        total_shifts = hist_shifts.get(i,0) + shifts_i
        total_hours = hist_hours.get(i,0) + hours_i

        scale = max(availability[i], 0.1)

        model.addConstr(total_shifts >= min_shifts * scale)
        model.addConstr(total_shifts <= max_shifts * scale)

        model.addConstr(total_hours >= min_hours * scale)
        model.addConstr(total_hours <= max_hours * scale)

        model.addConstr(score_i >= min_score * scale)
        model.addConstr(score_i <= max_score * scale)

        model.addConstr(weekend_i >= min_weekend * scale)
        model.addConstr(weekend_i <= max_weekend * scale)

    # =========================================================
    # OBJECTIVE
    # =========================================================
    request_term = gp.quicksum(
        works[i,j] for (i,j) in requests
        if i in employees and j in events
    )

    history_penalty = gp.quicksum(hist_shifts.get(i,0) for i in employees)
    change_penalty = gp.quicksum(change[i,j] for i in employees for j in events)

    model.setObjective(
        - W_SHIFTS * (max_shifts - min_shifts)
        - W_HOURS * (max_hours - min_hours)
        - W_SCORE * (max_score - min_score)
        - W_WEEKEND * (max_weekend - min_weekend)
        - W_HALLS * (max_halls - min_halls)
        - W_WEEKLY_BALANCE * (max_weekly - min_weekly)
        + REWARD_REQUEST * request_term
        - PENALTY_HISTORY * history_penalty
        - PENALTY_CHANGE * change_penalty,
        GRB.MAXIMIZE
    )

    # =========================================================
    # SOLVER
    # =========================================================
    model.setParam("MIPGap", 0.05)
    model.setParam("TimeLimit", 60)
    model.setParam("MIPFocus", 1)

    model.optimize()

    print("\n--- FULL MODEL DIAGNOSTICS ---\n")

    total_shifts = sum(works[i,j].X for i in employees for j in events)
    total_hours = sum(works[i,j].X * shift_dur[j] for i in employees for j in events)
    total_score = sum(works[i,j].X * shift_score[j] for i in employees for j in events)
    total_weekend = sum(works[i,j].X * weekend[j] for i in employees for j in events)

    for i in employees:

        name = dict_employees[i]["EmployeeName"]
        avail = availability[i]

        shifts = sum(works[i,j].X for j in events)
        hours = sum(works[i,j].X * shift_dur[j] for j in events)
        score = sum(works[i,j].X * shift_score[j] for j in events)
        weekend_count = sum(works[i,j].X * weekend[j] for j in events)

        # Expected (proportional)
        exp_shifts = avail * total_shifts / len(employees)
        exp_hours = avail * total_hours / len(employees)
        exp_score = avail * total_score / len(employees)
        exp_weekend = avail * total_weekend / len(employees)

        # Requests
        req_total = sum(1 for (ii,jj) in requests if ii == i)
        req_ok = sum(1 for (ii,jj) in requests if ii == i and works[ii,jj].X > 0.5)

        print(
            f"{name:12} | "
            f"Avail: {avail:.2f} | "
            f"S: {shifts:4.1f} ({exp_shifts:4.1f}) | "
            f"H: {hours:5.1f} ({exp_hours:5.1f}) | "
            f"Sc: {score:5.0f} ({exp_score:5.0f}) | "
            f"W: {weekend_count:3.1f} ({exp_weekend:3.1f}) | "
            f"Req: {req_ok}/{req_total}"
        )

    return model, works, shift_dur, weekend, weeks, event_date