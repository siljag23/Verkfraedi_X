import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from datetime import timedelta


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

    def to_hours(t):
        if hasattr(t, "total_seconds"):
            return t.total_seconds() / 3600
        else:
            return t.hour + t.minute / 60

    hist_shifts = hist_shifts or {}
    hist_hours = hist_hours or {}
    hist_halls = hist_halls or {}
    requests = requests or set()

    employees = list(dict_employees.keys())
    events = list(dict_events.keys())

    max_workhours_per_week = 48
    min_shifts_per_period = 3
    max_workdays_per_week = 6

    a,b,c,d,e,f,g,h,i,j,k,l = 90,91,100,101,90,91,30,31,50,51,70,71
    penalty_change = 200
    penalty_history = 20
    reward_request = 300

    emp_demand = {j: dict_events[j]["Employees"] for j in events}
    skill1_req = {j: dict_events[j]["Skillset1"] for j in events}
    skill2_req = {j: dict_events[j]["Skillset2"] for j in events}
    shift_score = {j: dict_events[j]["EventRanking"] for j in events}

    hall = {j: dict_events[j]["Hall"] for j in events}
    halls = list(set(hall.values()))

    start = {j: dict_events[j]["ShiftBegins"] for j in events}
    end = {j: dict_events[j]["ShiftEnds"] for j in events}

    event_date = {j: pd.to_datetime(dict_events[j]["Date"], dayfirst=True) for j in events}
    skill = {i: dict_employees[i]["Skillset"] for i in employees}

    weekend = {j: 1 if event_date[j].weekday() in [4,5,6] else 0 for j in events}
    weeks = sorted(set(event_date[j].isocalendar().week for j in events))

    # ---------------------------
    # Shift duration
    # ---------------------------
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

    # ---------------------------
    # Availability (NEW)
    # ---------------------------
    total_days = len(set(event_date[j].date() for j in events))

    availability = {}
    for i in employees:
        days_off = employee_days.get(i, set())
        available_days = total_days - len(days_off)

        if total_days > 0:
            availability[i] = available_days / total_days
        else:
            availability[i] = 1

    # ---------------------------
    # Vacation
    # ---------------------------
    vacation_events = [
        (i,j) for i in employees for j in events
        if event_date[j].date() in employee_days.get(i, set())
    ]

    # ---------------------------
    # Blocked pairs
    # ---------------------------
    blocked_pairs = set()
    shift_start = {}
    shift_end = {}

    for j in events:
        start_h = to_hours(start[j])
        shift_start[j] = event_date[j] + pd.to_timedelta(start_h, unit="h")
        shift_end[j] = shift_start[j] + pd.to_timedelta(shift_dur[j], unit="h")

    sorted_events = sorted(events, key=lambda j: shift_start[j])

    for idx, j1 in enumerate(sorted_events):
        for j2 in sorted_events[idx+1:]:

            if shift_start[j2] - shift_end[j1] >= timedelta(hours=13):
                break

            if event_date[j1].date() == event_date[j2].date():
                blocked_pairs.add((j1, j2))

            if shift_start[j2] > shift_end[j1] and (shift_start[j2] - shift_end[j1]) < timedelta(hours=13):
                blocked_pairs.add((j1, j2))

    # ---------------------------
    # Model
    # ---------------------------
    model = gp.Model("Event_staffing")

    works = model.addVars(employees, events, vtype=GRB.BINARY, name="works")
    change = model.addVars(employees, events, vtype=GRB.BINARY, name="change")

    # ---------------------------
    # Fairness variables
    # ---------------------------
    min_score = model.addVar()
    max_score = model.addVar()
    min_shifts = model.addVar()
    max_shifts = model.addVar()
    min_workhours = model.addVar()
    max_workhours = model.addVar()
    min_weekend = model.addVar()
    max_weekend = model.addVar()

    # ---------------------------
    # Demand
    # ---------------------------
    for j in events:
        model.addConstr(gp.quicksum(works[i,j] for i in employees) == emp_demand[j])

    # ---------------------------
    # Skills
    # ---------------------------
    for j in events:
        model.addConstr(gp.quicksum(works[i,j] for i in employees if skill[i] == 1) >= skill1_req[j])
        model.addConstr(gp.quicksum(works[i,j] for i in employees if skill[i] in [1,2]) >= skill2_req[j])

    for j in events:
        if emp_demand[j] == 1:
            model.addConstr(
                gp.quicksum(works[i,j] for i in employees if skill[i] == 3) == 0
            )

    # Vacation
    for (i,j) in vacation_events:
        model.addConstr(works[i,j] == 0)

    # Rest rules
    model.addConstrs(
        (works[i,j1] + works[i,j2] <= 1
         for i in employees
         for j1,j2 in blocked_pairs)
    )

    # ---------------------------
    # Availability-scaled constraints (FIX)
    # ---------------------------
    for i in employees:

        min_shifts_i = round(availability[i] * min_shifts_per_period)
        max_shifts_i = availability[i] * 10  # dynamic cap

        model.addConstr(
            gp.quicksum(works[i,j] for j in events) >= min_shifts_i
        )

        model.addConstr(
            gp.quicksum(works[i,j] for j in events) <= max_shifts_i
        )

    # ---------------------------
    # Weekly constraints
    # ---------------------------
    for i in employees:
        for week in weeks:
            model.addConstr(
                gp.quicksum(
                    works[i,j]
                    for j in events
                    if event_date[j].isocalendar().week == week
                ) <= max_workdays_per_week
            )

    for i in employees:
        for week in weeks:
            model.addConstr(
                gp.quicksum(
                    works[i,j] * shift_dur[j]
                    for j in events
                    if event_date[j].isocalendar().week == week
                ) <= max_workhours_per_week
            )

    # ---------------------------
    # Fairness (scaled)
    # ---------------------------
    for i in employees:

        current_shifts = gp.quicksum(works[i,j] for j in events)
        current_hours = gp.quicksum(works[i,j]*shift_dur[j] for j in events)
        current_weekend = gp.quicksum(works[i,j]*weekend[j] for j in events)

        scaled_shifts = current_shifts / max(availability[i], 0.1)
        scaled_hours = current_hours / max(availability[i], 0.1)
        scaled_weekend = current_weekend / max(availability[i], 0.1)

        model.addConstr(scaled_shifts >= min_shifts)
        model.addConstr(scaled_shifts <= max_shifts)

        model.addConstr(scaled_hours >= min_workhours)
        model.addConstr(scaled_hours <= max_workhours)

        model.addConstr(scaled_weekend >= min_weekend)
        model.addConstr(scaled_weekend <= max_weekend)

    # ---------------------------
    # Requests
    # ---------------------------
    request_term = gp.quicksum(
        works[i,j]
        for (i,j) in requests
        if i in employees and j in events
    )

    # ---------------------------
    # Objective (clean)
    # ---------------------------
    fairness = (
        a * min_shifts - d * max_shifts
        + e * min_workhours - f * max_workhours
        + i * min_weekend - j * max_weekend
    )

    penalties = penalty_history * gp.quicksum(
        hist_shifts.get(i,0) * gp.quicksum(works[i,j] for j in events)
        for i in employees
    )

    rewards = reward_request * request_term

    model.setObjective(
        fairness - penalties + rewards,
        GRB.MAXIMIZE
    )

    # Solver settings
    model.setParam("MIPGap", 0.02)
    model.setParam("TimeLimit", 60)
    model.setParam("MIPFocus", 1)

    model.optimize()

    return model, works, shift_dur, weekend, weeks, event_date