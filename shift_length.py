from datetime import datetime, timedelta

def  shift_length (start, end):

    today = datetime.today().date()

    start_date = datetime.combine(today, start)
    end_date = datetime.combine(today, end)

    if end_date < start_date:
        end_date += timedelta(days=1)

    return (end_date - start_date).total_seconds()/3600