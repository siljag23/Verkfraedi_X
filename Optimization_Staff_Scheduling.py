import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from datetime import timedelta
from itertools import combinations

def Optimization_Staff_Scheduling(dict_events, dict_employees, employee_days):

    # Indexar
    employees = list(dict_employees.keys())
    events = list(dict_events.keys())

    # Fastar kjarasamningar/reglur
    max_workhours_per_week = 48
    min_shifts_per_period = 1
    max_workdays_per_week = 6

    # Fastar, vægisstuðlar
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

    # Fastar gögn
    emp_demand = {j: dict_events[j]["Employees"] for j in events}
    skill1_req = {j: dict_events[j]["Skillset1"] for j in events}
    skill2_req = {j: dict_events[j]["Skillset2"] for j in events}
    shift_score = {j: dict_events[j]["EventRanking"] for j in events}
    hall = {j: dict_events[j]["Hall"] for j in events}
    start = {j: dict_events[j]["ShiftBegins"] for j in events}
    end = {j: dict_events[j]["ShiftEnds"] for j in events}
    event_date = {j: pd.to_datetime(dict_events[j]["Date"],dayfirst=True) for j in events}
    skill = {i: dict_employees[i]["Skillset"] for i in employees}
    weekend = {j: 1 if event_date[j].weekday() in [4,5,6] else 0 for j in events}
    weeks = sorted(set(event_date[j].isocalendar().week for j in events))

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
    
    # Listar
    # Frí
    vacation_events = []

    for i in employees:
        for j in events:

            if event_date[j].date() in employee_days.get(i, set()):
                vacation_events.append((i,j))

    # Banna 2 vaktir á dag og þarf að vera amk 13 klst á milli

    blocked_pairs = set()

    # precompute start/end time
    shift_start = {}
    shift_end = {}

    for j in events:

        shift_start[j] = event_date[j] + pd.to_timedelta(start[j].hour, unit="h") \
                        + pd.to_timedelta(start[j].minute, unit="m")

        shift_end[j] = shift_start[j] + pd.to_timedelta(shift_dur[j], unit="h")

    # sort events by start time
    sorted_events = sorted(events, key=lambda j: shift_start[j])

    for idx, j1 in enumerate(sorted_events):

        for j2 in sorted_events[idx+1:]:

            # ef meira en 13h á milli -> engin þörf að skoða fleiri
            if shift_start[j2] - shift_end[j1] >= timedelta(hours=13):
                break

            # sama dag
            if event_date[j1].date() == event_date[j2].date():
                blocked_pairs.add((j1, j2))

            # minna en 13h á milli
            if shift_start[j2] > shift_end[j1] and (shift_start[j2] - shift_end[j1]) < timedelta(hours=13):
                blocked_pairs.add((j1, j2))

    # Model
    model = gp.Model("Event_staffing")

    # Ákvörðunarbreyta
    works = model.addVars(employees,events,vtype=GRB.BINARY,name="works")

    # Sanngirnisbreytur
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

    # Skorður
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
    
    # Ekki vinna á frídögum
    for (i,j) in vacation_events:

        model.addConstr(
            works[i,j] == 0
        )
    
    # Banna event pör
    model.addConstrs(
        (works[i,j1] + works[i,j2] <= 1
        for i in employees
        for j1,j2 in blocked_pairs),
        name="blocked_pairs"
    )
    
    # Min 3 vaktir
    for i in employees:

        model.addConstr(
            gp.quicksum(works[i,j] for j in events) >= min_shifts_per_period
        )
    
    # Amk einn frídagur í viku
    
    for i in employees:
        for week in weeks:

            model.addConstr(
                gp.quicksum(
                    works[i,j]
                    for j in events
                    if event_date[j].isocalendar().week == week
                ) <= max_workdays_per_week
            )
    
    
    num_weeks = len(weeks)
    for i in employees:
        model.addConstr(
            gp.quicksum(
                works[i,j] * shift_dur[j]
                for j in events
            ) <= max_workhours_per_week * num_weeks
        )

    # Fairness skorður
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

    # Jafna vaktir milli vikna
    for week in weeks:

        model.addConstr(
            gp.quicksum(
                works[i,j]
                for i in employees
                for j in events
                if event_date[j].isocalendar().week == week
            )
            >= min_weekly_shifts
        )

        model.addConstr(
            gp.quicksum(
                works[i,j]
                for i in employees
                for j in events
                if event_date[j].isocalendar().week == week
            )
            <= max_weekly_shifts
        )

    # Markfall
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
    model.setParam("MIPGap", 0.05)
    model.setParam("TimeLimit", 60)
    model.setParam("MIPFocus", 1)

    # Leysa
    model.optimize()

    return model, works, shift_dur, weekend, weeks, event_date