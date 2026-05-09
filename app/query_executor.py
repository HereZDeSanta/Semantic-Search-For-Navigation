import pandas as pd
import numpy as np
from datetime import datetime, timedelta 
from .utils import format_timestamp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_aggregation(df: pd.DataFrame, metric: str):
    if df.empty:
        return {"error": "No data available"}
    
    if metric == "max_speed":
        max_speed_ms = df["horizontal_speed"].max()
        if pd.isna(max_speed_ms):
            return {"error": "No valid speed data"}
        
        max_speed_kmh = max_speed_ms * 3.6
        idx = df["horizontal_speed"].idxmax()
        ts = df.loc[idx, "_timestamp"]
        return {
            "max_speed": round(max_speed_kmh, 1),
            "units": "km/h",
            "timestamp": format_timestamp(int(ts))
        }
    elif metric == "avg_speed":
        avg_speed_ms = df["horizontal_speed"].mean()
        if pd.isna(avg_speed_ms):
            return {"error": "No valid speed data"}
        avg_speed_kmh = avg_speed_ms * 3.6
        return {"avg_speed": round(avg_speed_kmh, 1), "units": "km/h"}
    elif metric == "min_speed":
        min_speed_ms = df["horizontal_speed"].min()
        if pd.isna(min_speed_ms):
            return {"error": "No valid speed data"}
        min_speed_kmh = min_speed_ms * 3.6
        return {"min_speed": round(min_speed_kmh, 1), "units": "km/h"}
    else:
        return {"error": f"unknown metric {metric}"}

def execute_bad_position(df: pd.DataFrame):
    if 'pos_type__type' not in df.columns:
        return {"error": "pos_type__type column not found"}
    
    bad = df[df["pos_type__type"] == 19]
    total = len(bad)
    percent = (total / len(df)) * 100 if len(df) else 0
    
    points = []
    for _, row in bad.head(100).iterrows():
        points.append({
            "timestamp": format_timestamp(int(row["_timestamp"])),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "status": int(row["pos_type__type"]),
            "horizontal_speed": round(float(row["horizontal_speed"]) * 3.6, 1)
        })
    
    # Картинка
    from .visualize import plot_route
    image_url = plot_route(df, bad, title="Плохое качество позиционирования")
    
    return {
        "total_points": int(total),
        "percentage_of_trip": round(percent, 1),
        "points": points,
        "image": image_url
    }

def execute_time_slice(df: pd.DataFrame, start_hour: int, end_hour: int):
    if 'hour_moscow' not in df.columns:
        return {"error": "hour_moscow field not available"}
    
    mask = (df["hour_moscow"] >= start_hour) & (df["hour_moscow"] <= end_hour)
    subset = df[mask]
    
    if subset.empty:
        return {"message": f"No data between {start_hour}:00 and {end_hour}:00"}
    
    points = []
    for _, row in subset.iterrows():
        points.append({
            "timestamp": format_timestamp(int(row["_timestamp"])),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "horizontal_speed": round(float(row["horizontal_speed"]) * 3.6, 1)
        })
    
    # Картинка
    from .visualize import plot_route
    image_url = plot_route(df, subset, title=f"Точки в интервале {start_hour}:00-{end_hour}:00")
    
    return {
        "interval": f"{start_hour}:00-{end_hour}:00",
        "total_records": int(len(subset)),
        "points": points,
        "image": image_url
    }
    
    # return {
    #     "interval": f"{start_hour}:00-{end_hour}:00",
    #     "first_point": {
    #         "timestamp": format_timestamp(int(first["_timestamp"])),
    #         "latitude": float(first["latitude"]),
    #         "longitude": float(first["longitude"])
    #     },
    #     "last_point": {
    #         "timestamp": format_timestamp(int(last["_timestamp"])),
    #         "latitude": float(last["latitude"]),
    #         "longitude": float(last["longitude"])
    #     },
    #     "total_records": int(len(subset))
    # }

def execute_braking_events(df: pd.DataFrame, threshold: float):
    if 'acceleration' not in df.columns:
        return {"error": "acceleration field not available"}
    
    events = df[df["acceleration"] < threshold].dropna(subset=["acceleration"]).copy()
    total = len(events)
    
    if total == 0:
        return {
            "total_braking_events": 0,
            "max_deceleration": 0,
            "avg_deceleration": 0,
            "events": [],
            "image": None
        }
    
    max_dec = events["acceleration"].min()
    avg_dec = events["acceleration"].mean()
    
    events_list = []
    for idx, row in events.head(50).iterrows():
        idx_pos = df.index.get_loc(idx)
        if idx_pos > 0:
            prev_idx = df.index[idx_pos - 1]
            speed_before = df.loc[prev_idx, "horizontal_speed"] * 3.6
            speed_after = row["horizontal_speed"] * 3.6
        else:
            speed_before = row["horizontal_speed"] * 3.6
            speed_after = speed_before
        events_list.append({
            "timestamp": format_timestamp(int(row["_timestamp"])),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "deceleration": round(float(row["acceleration"]), 2),
            "speed_before": round(speed_before, 1),
            "speed_after": round(speed_after, 1)
        })
    
    # Картирнка
    from .visualize import plot_route
    image_url = plot_route(df, events, title=f"Резкое торможение (ускорение < {threshold} м/с²)")
    
    return {
        "total_braking_events": int(total),
        "max_deceleration": round(float(max_dec), 2),
        "avg_deceleration": round(float(avg_dec), 2),
        "events": events_list,
        "image": image_url
    }

def execute_geo_filter(df: pd.DataFrame, min_lat: float, max_lat: float, min_lon: float, max_lon: float):
    mask = (df["latitude"] >= min_lat) & (df["latitude"] <= max_lat) & \
           (df["longitude"] >= min_lon) & (df["longitude"] <= max_lon)
    subset = df[mask]
    
    if subset.empty:
        return {
            "total_points": 0,
            "message": "No points found in specified area",
            "image": None
        }
    
    points = []
    for _, row in subset.head(100).iterrows():
        points.append({
            "timestamp": format_timestamp(int(row["_timestamp"])),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"])
        })
    
    # Картинка
    from .visualize import plot_route
    image_url = plot_route(df, subset, title=f"Точки в области: широта [{min_lat}..{max_lat}], долгота [{min_lon}..{max_lon}]")
    
    return {
        "total_points": int(len(subset)),
        "points": points,
        "bounding_box": {
            "latitude": [min_lat, max_lat],
            "longitude": [min_lon, max_lon]
        },
        "image": image_url
    }