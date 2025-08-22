
from datetime import datetime, timedelta,UTC
import random
from zoneinfo import ZoneInfo
import argparse
import uuid
from prisma import Prisma

import asyncio

'''
    following scripts is for generating sample data 
    generates both the timestamp and business hour in utc timezone
    to run ->  python ./scripts/sample_data.py --days 10 --stores 2
'''

async def generate_sample_data(num_stores,num_days):
    start_hour = 8         
    end_hour = 17          
    timezones = ["America/New_York", "America/Chicago", "America/Los_Angeles", "America/Denver", "America/Phoenix"]


    stores = [f"{uuid.uuid4()}" for _ in range(1, num_stores+1)]
    store_hours = []
    store_timezone_map={}
    for store in stores:
        tz_str = random.choice(timezones)
        tz = ZoneInfo(tz_str)
        store_timezone_map[store]=tz_str
        for day in range(7):
            start_hour = random.randint(8, 10)
            end_hour = random.randint(17, 19)
            start_local = datetime(1970, 1, 1, start_hour, 0, tzinfo=tz)
            end_local   = datetime(1970, 1, 1, end_hour, 0, tzinfo=tz)
            start_dt = start_local.astimezone(UTC)
            end_dt   = end_local.astimezone(UTC)

            store_hours.append({
                "storeId": store,
                "dayOfWeek": day,
                "startTime": start_dt,
                "endTime": end_dt
            })

    store_status = []
    for store in stores:
        tz_str = store_timezone_map[store]
        for day_offset in range(num_days):
            date = datetime.now(UTC) - timedelta(days=day_offset)
            for hour in range(start_hour, end_hour+1):
                local_dt = datetime(year=date.year, month=date.month, day=date.day, hour=hour, minute=date.minute, tzinfo=ZoneInfo(tz_str))
                utc_dt = local_dt.astimezone(UTC) 
                store_status.append({
                    "storeId": store,
                    "timestamp": utc_dt,
                    "status": random.choice(["ACTIVE","INACTIVE"])
                })




    store_timezones = []
    for store in stores:
        tz_str = store_timezone_map[store]
        store_timezones.append({
            "storeId": store,
            "timezone": tz_str
        })

    prisma=Prisma()

    await prisma.connect()

    # #  to refresh data
    await prisma.storehours.delete_many()
    await prisma.storetimezone.delete_many()
    await prisma.storestatus.delete_many()


    await prisma.storestatus.create_many(data=store_status)
    await prisma.storetimezone.create_many(data=store_timezones)
    await prisma.storehours.create_many(data=store_hours)
    await prisma.disconnect()
    
    print(f"Generated {num_stores} stores with {num_days} days of data each.")
    




if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--stores")
    parser.add_argument("--days")
    args=parser.parse_args()
    num_stores=int(args.stores)
    num_days=int(args.days)
    asyncio.run(generate_sample_data(num_days=num_days,num_stores=num_stores))


