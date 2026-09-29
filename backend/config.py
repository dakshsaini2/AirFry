import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./apix.db")

# Lead times (days before departure)
LEAD_TIMES = [1, 7, 15, 30, 45]

# Departure buckets configuration
# For matching a given hour to a bucket
def get_departure_bucket(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"
