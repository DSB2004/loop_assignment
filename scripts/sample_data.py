
from datetime import datetime, timedelta
import random
import pytz
import os
import argparse
import uuid
from prisma import Prisma

import asyncio

    


async def generate_sample_data(num_stores,num_days):
    os.makedirs("assets",exist_ok=True)
    start_hour = 8         
    end_hour = 17          
    timezones = ["America/New_York", "America/Chicago", "America/Los_Angeles", "America/Denver", "America/Phoenix"]


    stores = [f"{uuid.uuid4()}" for _ in range(1, num_stores+1)]

    print("stores",len(stores))
    store_status = []
    for store in stores:
        for day_offset in range(num_days):
            date = datetime.utcnow() - timedelta(days=day_offset)
            for hour in range(start_hour, end_hour+1):
                ts = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                store_status.append({
                    "storeId": store,
                    "timestamp": ts.isoformat() + "Z",
                    "status": random.choice(["ACTIVE", "ACTIVE","ACTIVE","ACTIVE","INACTIVE"])
                })

    store_hours = []
    for store in stores:
        tz_str = random.choice(timezones)
        tz = pytz.timezone(tz_str)
        for day in range(7):
            start_hour_local = random.randint(8, 10)
            end_hour_local = random.randint(17, 19)
            today = datetime.now(tz)
            start_dt = tz.localize(datetime(today.year, today.month, today.day, start_hour_local))
            end_dt = tz.localize(datetime(today.year, today.month, today.day, end_hour_local))

            start_dt_utc = start_dt.astimezone(pytz.UTC).replace(tzinfo=None)
            end_dt_utc = end_dt.astimezone(pytz.UTC).replace(tzinfo=None)

            store_hours.append({
                "storeId": store,
                "dayOfWeek": day,
                "startTime": start_dt_utc,
                "endTime": end_dt_utc
            })



    store_timezones = []
    for store in stores:
        tz_str = random.choice(timezones)
        store_timezones.append({
            "storeId": store,
            "timezone": tz_str
        })

    prisma=Prisma()

    await prisma.connect()
    
    # # #  to refresh data
    # await prisma.storehours.delete_many()
    # await prisma.storetimezone.delete_many()
    # await prisma.storestatus.delete_many()


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



# Run this -> python ./scripts/sample_data.py --days 60 --stores 20