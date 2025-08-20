from prisma import Prisma
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import csv
import os

#  to run -> python ./src/worker.py

def get_range(today, store_business_hour, tz, start, end):
    day_of_week = today.weekday()
    bh_start_template = None
    bh_end_template = None

    if day_of_week not in store_business_hour:
        bh_start_template = datetime(year=today.year, month=today.month, day=today.day, hour=0, minute=0, tzinfo=tz)
        bh_end_template = datetime(year=today.year, month=today.month, day=today.day, hour=23, minute=59, tzinfo=tz)
    else:
        bh_start_template = store_business_hour[day_of_week]['start']
        bh_end_template = store_business_hour[day_of_week]['end']

    bh_start = bh_start_template.replace(
        year=today.year, month=today.month, day=today.day
    )
    bh_end = bh_end_template.replace(
        year=today.year, month=today.month, day=today.day
    )
    
    bh_start = max(bh_start, start)
    bh_end = min(bh_end, end)

    return {"start": bh_start, "end": bh_end}

async def calculate_uptime_downtime(
        db,
        store_tz,
        store_id,
        store_business_hour,
        start_datetime, 
        end_datetime
    ):
    uptime = timedelta()
    downtime = timedelta()
    fulltime = 0
    tz = ZoneInfo(store_tz)
    
    logs = await db.storestatus.find_many(
        where={
            'storeId': store_id,
            'timestamp': {'gte': start_datetime, 'lte': end_datetime}
        },
        order={'timestamp': 'asc'}
    )

    current_day = start_datetime.date()
    end_day = end_datetime.date()

    while current_day <= end_day:
        time_range = get_range(
            today=current_day,
            store_business_hour=store_business_hour,
            tz=tz,
            start=start_datetime,
            end=end_datetime
        )
        bh_start = time_range['start']
        bh_end = time_range['end']
        
        fulltime += (bh_end - bh_start).total_seconds()
        day_logs = [log for log in logs if bh_start <= log.timestamp.astimezone(tz) <= bh_end]
        day_logs.sort(key=lambda x: x.timestamp)
        
        last_ts = bh_start
        for log in day_logs:
            ts = log.timestamp.astimezone(tz)
            delta = ts - last_ts
            if log.status == "ACTIVE":
                uptime += delta
            else:
                downtime += delta
            last_ts = ts

        if last_ts < bh_end:
            delta = bh_end - last_ts
            if day_logs and day_logs[-1].status == "ACTIVE":
                uptime += delta
            else:
                downtime += delta

        current_day += timedelta(days=1) 

    return {
        "full_hours": fulltime / 3600,
        "uptime_hours": uptime.total_seconds() / 3600,
        "downtime_hours": downtime.total_seconds() / 3600
    }

async def generate_report_task(store_id,report_id):
    db = Prisma()
    await db.connect()
    
    try:
        tz_data = await db.storetimezone.find_unique(where={'storeId': store_id})
        tz = tz_data.timezone if tz_data else "America/Chicago"
        now = datetime.now(ZoneInfo(tz))
        
        store_hours = await db.storehours.find_many(where={'storeId': store_id})
        store_day_to_hour = {}
        for day in store_hours:
            store_day_to_hour[day.dayOfWeek] = {
                'start': day.startTime.astimezone(ZoneInfo(tz)),
                'end': day.endTime.astimezone(ZoneInfo(tz))
            }
        
        last_hour_stats = await calculate_uptime_downtime(
            db, tz, store_id, store_day_to_hour, now - timedelta(hours=1), now
        )
        
        last_day_stats = await calculate_uptime_downtime(
            db, tz, store_id, store_day_to_hour, now - timedelta(days=1), now
        )
        
        last_week_stats = await calculate_uptime_downtime(
            db, tz, store_id, store_day_to_hour, now - timedelta(days=7), now
        )
        os.makedirs("/reports",exist_ok=True)
        with open(f"./reports/report-{store_id}.csv","w") as file:
            writer=csv.writer(file)

            writer.writerow(["store_id","uptime_last_hour","uptime_last_day","uptime_last_week","downtime_last_hour","downtime_last_day","downtime_last_week"])
            writer.writerow([store_id,last_hour_stats["uptime_hours"]*60,last_day_stats["uptime_hours"],last_week_stats["uptime_hours"],last_hour_stats["downtime_hours"]*60,last_day_stats["downtime_hours"],last_week_stats["downtime_hours"]])
        

        await db.reports.update(where={
            "id":report_id,
        },data={
            "status":"SUCCESSFUL",
            "report":f"report-{store_id}-{report_id}.csv"
        })


        print("Last Hour:", last_hour_stats)
        print("Last Day:", last_day_stats)
        print("Last Week:", last_week_stats)

    finally:
        await db.disconnect()
