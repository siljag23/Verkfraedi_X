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
    hist_halls=None
):

    hist_shifts = hist_shifts or {}
    hist_hours = hist_hours or {}
    hist_halls = hist_halls or {}

    employees = list(dict_employees.keys())
    events = list(dict_events.keys())

    max_workhours_per_week = 48
    min_shifts_per_period = 3
    max_workdays_per_week = 6

    a,b,c,d,e,f,g,h,i,j,k,l = 90,91,100,101,90,91,30,31,50,51,70,71

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

    shift_dur = {}
    for j in events:
        start_h = start[j].hour + start[j].minute/60
        end_h = end[j].hour + end[j].minute/60
        if end_h < start_h:
            end_h += 24
        shift_dur[j] = end_h - start_h

    vacation_events = [
        (i,j) for i in employees for j in events
        if event_date[j].date() in employee_days.get(i, set())
    ]

    blocked_pairs = set()
    shift_start = {}
    shift_end = {}

    for j in events:
        shift_start[j] = event_date[j] + pd.to_timedelta(start[j].hour, unit="h") \
                        + pd.to_timedelta(start[j].minute, unit="m")
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

    model = gp.Model("Event_staffing")

    works = model.addVars(employees, events, vtype=GRB.BINARY, name="works")

    min_score = model.addVar()
    max_score = model.addVar()
    min_shifts = model.addVar()
    max_shifts = model.addVar()
    min_workhours = model.addVar()
    max_workhours = model.addVar()
    min_weekend = model.addVar()
    max_weekend = model.addVar()
    min_halls = model.addVar()
    max_halls = model.addVar()
    min_weekly_shifts = model.addVar()
    max_weekly_shifts = model.addVar()

    # Demand
    for j in events:
        model.addConstr(gp.quicksum(works[i,j] for i in employees) == emp_demand[j])

    # Skill
    for j in events:
        model.addConstr(gp.quicksum(works[i,j] for i in employees if skill[i] == 1) >= skill1_req[j])
        model.addConstr(gp.quicksum(works[i,j] for i in employees if skill[i] in [1,2]) >= skill2_req[j])

    # Skill 3 má ekki vera einn
    for j in events:
        if emp_demand[j] == 1:
            model.addConstr(
                gp.quicksum(works[i,j] for i in employees if skill[i] == 3) == 0
            )

    # Vacation
    for (i,j) in vacation_events:
        model.addConstr(works[i,j] == 0)

    # Blocked pairs
    model.addConstrs(
        (works[i,j1] + works[i,j2] <= 1
         for i in employees
         for j1,j2 in blocked_pairs)
    )

    # Min shifts
    for i in employees:
        model.addConstr(gp.quicksum(works[i,j] for j in events) >= min_shifts_per_period)

    # Weekly rest
    for i in employees:
        for week in weeks:
            model.addConstr(
                gp.quicksum(works[i,j] for j in events if event_date[j].isocalendar().week == week)
                <= max_workdays_per_week
            )

    # Max hours
    num_weeks = len(weeks)
    for i in employees:
        model.addConstr(
            gp.quicksum(works[i,j] * shift_dur[j] for j in events)
            <= max_workhours_per_week * num_weeks
        )

    # FAIRNESS (CURRENT + HISTORY)
    for i in employees:

        current_shifts = gp.quicksum(works[i,j] for j in events)
        current_hours = gp.quicksum(works[i,j]*shift_dur[j] for j in events)
        current_weekend = gp.quicksum(works[i,j]*weekend[j] for j in events)

        total_shifts = hist_shifts.get(i,0) + current_shifts
        total_hours = hist_hours.get(i,0) + current_hours

        # Score
        model.addConstr(gp.quicksum(works[i,j]*shift_score[j] for j in events) >= min_score)
        model.addConstr(gp.quicksum(works[i,j]*shift_score[j] for j in events) <= max_score)

        # Shifts
        model.addConstr(total_shifts >= min_shifts)
        model.addConstr(total_shifts <= max_shifts)

        # Hours
        model.addConstr(total_hours >= min_workhours)
        model.addConstr(total_hours <= max_workhours)

        # Weekend
        model.addConstr(current_weekend >= min_weekend)
        model.addConstr(current_weekend <= max_weekend)

        # Halls
        for h in halls:
            current_h = gp.quicksum(works[i,j] for j in events if hall[j] == h)
            total_h = hist_halls.get(i, {}).get(h, 0) + current_h

            model.addConstr(total_h >= min_halls)
            model.addConstr(total_h <= max_halls)

    # Weekly balance
    for week in weeks:
        total_week = gp.quicksum(
            works[i,j]
            for i in employees
            for j in events
            if event_date[j].isocalendar().week == week
        )
        model.addConstr(total_week >= min_weekly_shifts)
        model.addConstr(total_week <= max_weekly_shifts)

    model.setObjective(
        a*min_score - b*max_score
        + c*min_shifts - d*max_shifts
        + e*min_workhours - f*max_workhours
        + g*min_halls - h*max_halls
        + i*min_weekend - j*max_weekend
        + k*min_weekly_shifts - l*max_weekly_shifts,
        GRB.MAXIMIZE
    )

    model.setParam("MIPGap", 0.05)
    model.setParam("TimeLimit", 60)
    model.setParam("MIPFocus", 1)

    model.optimize()

    return model, works, shift_dur, weekend, weeks, event_date