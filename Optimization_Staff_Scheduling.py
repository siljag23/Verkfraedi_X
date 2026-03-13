import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from datetime import timedelta

def Optimization_Staff_Scheduling(dict_events, dict_employees, employee_days):

    # Indexar
    employees = list(dict_employees.keys())
    events = list(dict_events.keys())

    # Fastar kjarasamningar/reglur
    max_workhours_per_day = 11
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
    weekend = {j: 1 if event_date[j].weekday() in [4,5] else 0 for j in events}
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

    for j1 in events:
        for j2 in events:

            if j1 < j2:

                if event_date[j1].date() == event_date[j2].date():

                    blocked_pairs.add((j1,j2))

    for j1 in events:
        for j2 in events:

            if j1 != j2:

                end1 = event_date[j1] + pd.to_timedelta(start[j1].hour,unit="h")
                end1 += pd.to_timedelta(start[j1].minute,unit="m")
                end1 += pd.to_timedelta(shift_dur[j1],unit="h")

                start2 = event_date[j2] + pd.to_timedelta(start[j2].hour,unit="h")
                start2 += pd.to_timedelta(start[j2].minute,unit="m")

                if start2 > end1 and (start2 - end1) < timedelta(hours=13):

                    blocked_pairs.add((j1,j2))

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
    for i in employees:
        for j1,j2 in blocked_pairs:

            model.addConstr(
                works[i,j1] + works[i,j2] <= 1
            )
    """
    # Max 11 klst á dag
    days = sorted(set(event_date[j].date() for j in events))

    for i in employees:
        for day in days:

            model.addConstr(
                gp.quicksum(
                    works[i,j]*shift_dur[j]
                    for j in events
                    if event_date[j].date() == day
                ) <= max_workhours_per_day
            )
    """
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
    model.setParam("MIPGap",0.05)

    # Leysa
    model.optimize()

    if model.status == GRB.INFEASIBLE:
        print("\nModel is infeasible. Computing IIS...\n")
        model.computeIIS()

        print("Constraints causing infeasibility:")
        for c in model.getConstrs():
            if c.IISConstr:
                print(" -", c.ConstrName)

        # valfrjálst: skrifa í skrá
        model.write("infeasible_model.ilp")

    return model, works, shift_dur, weekend, weeks, event_date