from pydantic import BaseModel
from typing import List, Optional, Union, Any

class QueryRequest(BaseModel):
    query: str

class AggregationResult(BaseModel):
    max_speed: Optional[float] = None
    avg_speed: Optional[float] = None
    units: str = "km/h"
    timestamp: Optional[str] = None

class BadPositionPoint(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    status: int
    horizontal_speed: float

class BadPositionResult(BaseModel):
    total_points: int
    percentage_of_trip: float
    points: List[BadPositionPoint] = []

class BrakingEvent(BaseModel):
    timestamp: str
    latitude: float
    longitude: float
    deceleration: float
    speed_before: float
    speed_after: float

class BrakingResult(BaseModel):
    total_braking_events: int
    max_deceleration: float
    avg_deceleration: float
    events: List[BrakingEvent] = []

class GenericResponse(BaseModel):
    status: str
    query: str
    result: Any