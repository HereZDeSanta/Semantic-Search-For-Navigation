import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-120b:free"
DATA_PATH = os.getenv("DATA_PATH", "data/data.csv")


# Параметры для разных типов запросов (для парсера)
TWILIGHT_HOURS = {
    "start_hour": 16,
    "end_hour": 19
}

BRAKING_THRESHOLD = -2.0

M11_BOUNDS = {
    "min_lat": 59,
    "max_lat": 60,
    "min_lon": 30.33,
    "max_lon": 37
}