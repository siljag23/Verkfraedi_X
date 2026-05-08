import pandas as pd

def To_Hours(t):
    # timedelta
    if hasattr(t, "total_seconds"):
        return t.total_seconds() / 3600

    # datetime.time eða datetime
    if hasattr(t, "hour"):
        return t.hour + t.minute / 60

    # fallback
    try:
        t = pd.to_datetime(t)
        return t.hour + t.minute / 60
    except:
        return 0


def Compute_Shift_Duration(dict_events):
    shift_dur = {}

    for j, event in dict_events.items():
        start = event["ShiftBegins"]
        end = event["ShiftEnds"]

        start_h = To_Hours(start)
        end_h = To_Hours(end)

        if end_h < start_h:
            end_h += 24

        dur = end_h - start_h
        shift_dur[j] = dur

    return shift_dur