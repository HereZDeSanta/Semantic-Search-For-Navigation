import json
from .llm_client import call_llm

PROMPT_TEMPLATE = """
Ты - эксперт по анализу навигационных данных беспилотного тягача.
Данные содержат следующие поля: latitude, longitude, north_velocity, east_velocity,
pos_type__type, _timestamp, horizontal_speed, acceleration, hour_moscow.

Пользователь спрашивает: "{query}"

Твоя задача - определить тип запроса. Отвечай ТОЛЬКО В ФОРМАТЕ JSON (без пояснений, без markdown и прочего).

Возможные типы данных:
- aggregation (для max_speed, avg_speed, min_speed)
- filter_bad_position (pos_type__type == 19)
- time_slice (сумерки, вечер, утро, ночь) - нужны start_hour, end_hour (Сумерками считаются отрезок от 16 до 19)
- braking_events (резкое торможение) - порог threshold в (м/с)^2 (отрицательный(со знаком "минус"))
- geo_filter (координатный прямоугольник) - поля min_lat, max_lat, min_lon, max_lon. Запросы будут связаны с запросами "трасса", "м11" и их альтернативы.

Примеры для понимания:
{{"type": "aggregation", "metric": "max_speed"}}
{{"type": "filter_bad_position"}}
{{"type": "time_slice", "start_hour": 16, "end_hour": 19}}
{{"type": "braking_events", "threshold": -2.0}}
{{"type": "geo_filter", "min_lat": 55.5, "max_lat": 60.0, "min_lon": 30.0, "max_lon": 37.5}}

Если запрос не подходит — верни ответ {{"type": "unknown"}}.
"""

async def parse_query(user_query: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(query=user_query)
    raw = await call_llm(prompt)
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"type": "unknown"}