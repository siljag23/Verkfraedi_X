import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from datetime import timedelta
import numpy as np


def Optimization_Staff_Scheduling2(
    dict_events,
    dict_employees,
    employee_days,
    hist_shifts=None,
    hist_hours=None,
    hist_halls=None,
    hist_weekend=None,
    current_schedule=None,
    requests=None
):

    employees = list(dict_employees.keys())
    events = list(dict_events.keys())

    hist_shifts = hist_shifts or {}
    hist_hours = hist_hours or {}
    hist_halls = hist_halls or {}
    hist_weekend = hist_weekend or {}
    requests = requests or set()

    MAX_WORKHOURS_PER_WEEK = 48
    MAX_WORKDAYS_PER_WEEK = 6

    W_SHIFTS = 1
    W_HOURS = 5
    W_SCORE = 0.8
    W_WEEKEND = 5
    W_HALLS = 0.5
    W_WEEKLY_BALANCE = 0.7

    REWARD_REQUEST = 10
    PENALTY_HISTORY = 0.5

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

    shift_start = {}
    shift_end = {}

    for j in events:
        start_h = to_hours(start[j])
        shift_start[j] = event_date[j] + pd.to_timedelta(start_h, unit="h")
        shift_end[j] = shift_start[j] + pd.to_timedelta(shift_dur[j], unit="h")

    blocked_pairs = set()
    sorted_events = sorted(events, key=lambda j: shift_start[j])

    for idx, j1 in enumerate(sorted_events):
        for j2 in sorted_events[idx+1:]:

            rest_time = shift_start[j2] - shift_end[j1]

            if rest_time >= timedelta(hours=11):
                break

            blocked_pairs.add((j1, j2))

    total_days = len(set(event_date[j].date() for j in events))

    availability = {}
    scale = {}

    for i in employees:
        days_off = employee_days.get(i, set())
        availability[i] = (total_days - len(days_off)) / total_days if total_days > 0 else 1
        scale[i] = max(availability[i], 0.1)

    model = gp.Model("Event_staffing")

    works = model.addVars(employees, events, vtype=GRB.BINARY, name="works")
    works_hall = model.addVars(employees, halls, vtype=GRB.BINARY, name="works_hall")

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
        model.addConstr(
            gp.quicksum(works[i,j] for j in events) >= availability[i] * 3
        )

    for i in employees:
        for d in set(event_date[j].date() for j in events):
            model.addConstr(
                gp.quicksum(
                    works[i,j]
                    for j in events
                    if event_date[j].date() == d
                ) <= 1
            )

    model.addConstrs(
        (works[i,j1] + works[i,j2] <= 1
        for i in employees
        for (j1,j2) in blocked_pairs)
    )

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

    for i in employees:
        for j in events:
            model.addConstr(works[i,j] <= works_hall[i, hall[j]])

    for i in employees:
        total_halls = gp.quicksum(works_hall[i,h] for h in halls) + sum(hist_halls.get(i, {}).values())
        model.addConstr(total_halls >= min_halls)
        model.addConstr(total_halls <= max_halls)

    for i in employees:

        shifts_i = gp.quicksum(works[i,j] for j in events)
        hours_i = gp.quicksum(works[i,j]*shift_dur[j] for j in events)
        score_i = gp.quicksum(works[i,j]*shift_score[j] for j in events)
        weekend_i = gp.quicksum(works[i,j]*weekend[j] for j in events)
        total_weekend_i = hist_weekend.get(i, 0) + weekend_i

        model.addConstr(shifts_i >= min_shifts * scale[i])
        model.addConstr(shifts_i <= max_shifts * scale[i])

        model.addConstr(hours_i >= min_hours * scale[i])
        model.addConstr(hours_i <= max_hours * scale[i])

        model.addConstr(score_i >= min_score * scale[i])
        model.addConstr(score_i <= max_score * scale[i])

        model.addConstr(total_weekend_i >= min_weekend)
        model.addConstr(total_weekend_i <= max_weekend)

    min_hall = {h: model.addVar() for h in halls}
    max_hall = {h: model.addVar() for h in halls}

    for h in halls:
        for i in employees:

            y_i_h = gp.quicksum(
                works[i,j] for j in events if hall[j] == h
            )

            model.addConstr(y_i_h >= min_hall[h] * scale[i])
            model.addConstr(y_i_h <= max_hall[h] * scale[i])

    request_term = gp.quicksum(
        works[i,j] for (i,j) in requests
        if i in employees and j in events
    )

    avg_hist = sum(hist_shifts.get(i,0) for i in employees) / len(employees)

    history_balance = gp.quicksum(
        ((hist_shifts.get(i,0) - avg_hist) / scale[i]) *
        gp.quicksum(works[i,j] for j in events)
        for i in employees
    )

    model.setObjective(
        - W_SHIFTS * (max_shifts - min_shifts)
        - W_HOURS * (max_hours - min_hours)
        - W_SCORE * (max_score - min_score)
        - W_WEEKEND * (max_weekend - min_weekend)
        - W_HALLS * gp.quicksum(max_hall[h] - min_hall[h] for h in halls)
        - W_WEEKLY_BALANCE * (max_weekly - min_weekly)
        + REWARD_REQUEST * request_term
        - PENALTY_HISTORY * history_balance,
        GRB.MAXIMIZE
    )

    model.setParam('MIPGap', 0.03)
    model.setParam('TimeLimit', 60)  

    model.optimize()

    return model, works, shift_dur, weekend, weeks, event_date