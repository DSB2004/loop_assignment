import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
redis_url =  os.getenv("REDIS_URL")
