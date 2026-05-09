import json
import re
from .llm_client import call_llm
from .config import TWILIGHT_HOURS, BRAKING_THRESHOLD, M11_BOUNDS


PROMPT_TEMPLATE = """
Ты - эксперт по анализу навигационных данных беспилотного тягача.
Данные содержат следующие поля: latitude, longitude, north_velocity, east_velocity,
pos_type__type, _timestamp, horizontal_speed, acceleration, hour_moscow.

Пользователь спрашивает: "{query}"

Твоя задача - определить тип запроса. Отвечай ТОЛЬКО В ФОРМАТЕ JSON (без пояснений, без markdown и прочего).

Возможные типы данных:
- aggregation (для max_speed, avg_speed, min_speed)
- filter_bad_position (pos_type__type == 19)
- time_slice (сумерки, вечер, утро, ночь) - нужны start_hour, end_hour
- braking_events (резкое торможение) - порог threshold в (м/с)^2 (отрицательный(со знаком "минус"))
- geo_filter (запросы про трассу М11, шоссе, координаты) - к ним относятся данные min_lat, max_lat, min_lon, max_lon.

Примеры ответов:
{{"type": "aggregation", "metric": "max_speed"}}
{{"type": "aggregation", "metric": "avg_speed"}}
{{"type": "filter_bad_position"}}
{{"type": "time_slice"}}
{{"type": "braking_events"}}
{{"type": "geo_filter"}}

Если запрос не подходит — верни ответ {{"type": "unknown"}}.
"""

async def parse_query(user_query: str) -> dict:
    query_lower = user_query.lower()

    # Метод rule-based для частых запросов

    # М11
    if any(word in query_lower for word in ['м11', 'трасса', 'm11', 'трасса м11', 'М-11']):
        return {"type": "geo_filter", **M11_BOUNDS}
    
    # Сумерки
    if any(word in query_lower for word in ['сумерки', 'dusk', 'twilight', 'вечер']):
        return {"type": "time_slice", **TWILIGHT_HOURS}
    
    # Резкое торможение
    if any(word in query_lower for word in ['тормоз', 'braking', 'deceleration', 'резко', 'торможение']):
        return {"type": "braking_events", "threshold": BRAKING_THRESHOLD}
    
    # Утро
    if any(word in query_lower for word in ['утро', 'morning']):
        return {"type": "time_slice", "start_hour": 6, "end_hour": 12}
    
    # День
    if any(word in query_lower for word in ['день', 'daytime']):
        return {"type": "time_slice", "start_hour": 12, "end_hour": 15}
    
    # Ночь
    if any(word in query_lower for word in ['ночь', 'night']):
        return {"type": "time_slice", "start_hour": 22, "end_hour": 5}



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
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"type": "unknown"}
    
    qtype = parsed.get("type")
    
    if qtype == "time_slice":
        parsed.update(TWILIGHT_HOURS)
    elif qtype == "braking_events":
        parsed["threshold"] = BRAKING_THRESHOLD
    elif qtype == "geo_filter":
        parsed.update(M11_BOUNDS)
    
    return parsed