from prisma import Prisma
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import csv
import os

'''
    To run: python ./src/worker.py
'''

'''
    store_business_hour -> thats stores the business hour in utc on a particular week day for a store
    start -> start of range, basically for a week it goes from a week past today at the same time the request was made
    end -> end of range,  basically today
'''

'''
    what this function get_range do is based on tz and start/end range it returns the start and end timeline for a day
'''

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

    
    '''
        because the start and time in db have 1970 january 1st as date since we didn't need them
    '''

    bh_start = bh_start_template.replace(
        year=today.year, month=today.month, day=today.day
    )
    bh_end = bh_end_template.replace(
        year=today.year, month=today.month, day=today.day
    )

    '''
        done to get the required range, as incase we are calculating at the middle of the business hour then we only consider timestamps from middle of day a week past of a day past

        we can set them to start and end directly if we wish to consider the past hours for the starting day 
    '''

    bh_start = max(bh_start, start)
    bh_end = min(bh_end, end)

    '''
        edge case incase the last hour goes beyond the business hour 
        i.e 
            business hour 9 am to 5 pm
            and request made at 9:30 pm will consider 8:30 pm to 9:30 pm
            and this lead to inverted timestamp causing negative calculation
    '''

    if bh_start >= bh_end:
        return None  


    return {"start": bh_start, "end": bh_end}


'''
    returns fulltime, uptime and downtime of store in a given interval
'''

async def calculate_uptime_downtime(
        db,
        store_tz,
        store_id,
        store_business_hour,
        start_datetime, 
        end_datetime
    ):

    '''
        uptime and downtime for that respected period and fulltime is how much the total business second were there in
        the given time range (hours, days or even week)
    '''

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

        '''
            this is to cover case when the time interval is outside the business hour, mostly incase of last hour,
            same is described in the calculate_uptime_downtime function
        '''
        if time_range is None:
            current_day += timedelta(days=1) 
            continue

        bh_start = time_range['start']
        bh_end = time_range['end']


        
        '''
            to get the logs for each day as we are pooling every hour we get logs for each hours every day
        '''

        day_logs = [log for log in logs if bh_start <= log.timestamp.astimezone(tz) <= bh_end]
        day_logs.sort(key=lambda x: x.timestamp)

        '''
            here we start iterating each log to check for ACTIVE and INACTIVE status

            here the last_ts acts as a reference points and status of store from last_ts to next timestamp will be considered based on the last timestamp status 

            i.e 
                for last_ts -> 9:00 AM  as ACTIVE
                and next_ts -> 10:01 AM as INACTIVE

                the store is considered to be active from 9:00 AM to 10:01 AM after which its status becomes INACTIVE till the next timestamp or end of business hour , if thats before the next timestamp (before 1 hour)

        '''
        
        '''
            incase no log found for that time being we wont be adding that in the uptime or downtime,
            could be that store status data is not present for that time interval
        '''

        if len(day_logs)==0:
            current_day += timedelta(days=1)
            continue        

        fulltime += (bh_end - bh_start).total_seconds()
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

        '''
            moves to next date
        '''

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
        os.makedirs("reports",exist_ok=True)
        with open(f"./reports/report-{report_id}.csv","w") as file:
            writer=csv.writer(file)

            writer.writerow(["store_id","uptime_last_hour","uptime_last_day","uptime_last_week","downtime_last_hour","downtime_last_day","downtime_last_week"])
            writer.writerow([store_id,last_hour_stats["uptime_hours"]*60,last_day_stats["uptime_hours"],last_week_stats["uptime_hours"],last_hour_stats["downtime_hours"]*60,last_day_stats["downtime_hours"],last_week_stats["downtime_hours"]])
        

        await db.reports.update(where={
            "id":report_id,
        },data={
            "status":"SUCCESSFUL",
            "report":f"report-{report_id}.csv"
        })


        print("Last Hour:", last_hour_stats)
        print("Last Day:", last_day_stats)
        print("Last Week:", last_week_stats)

    except Exception as e:
        print(f"Error happended {e}")
        if not db.is_connected:
            print("Failed to get database connection")
        else:
             await db.reports.update(where={
                "id":report_id,
                },data={
                    "status":"FAILED",
                })
    finally:
          if db.is_connected:
            await db.disconnect()
