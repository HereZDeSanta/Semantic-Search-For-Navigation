import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("_timestamp").copy()

    logger.info(f"Sample timestamp (nanoseconds): {df['_timestamp'].iloc[0] if len(df) > 0 else 'N/A'}")
    
    # Конвертируем timestamp в сеунды
    df["_timestamp_sec"] = df["_timestamp"] // 1_000_000_000

    logger.info(f"Timestamp range (seconds): {df['_timestamp_sec'].min()} - {df['_timestamp_sec'].max()}")
    
    # Горизонтальная скорость
    df["horizontal_speed"] = np.sqrt(df["north_velocity"]**2 + df["east_velocity"]**2)
    
    # Ускорение
    dt = df["_timestamp_sec"].diff()
    dv = df["horizontal_speed"].diff()
    df["acceleration"] = dv / dt
    
    # Переход на время по МСК
    df["datetime_moscow"] = pd.to_datetime(df["_timestamp_sec"], unit='s') + pd.Timedelta(hours=3)
    df["hour_moscow"] = df["datetime_moscow"].dt.hour

    df["_timestamp"] = df["_timestamp_sec"]
    
    logger.info(f"Final dataframe shape: {df.shape}")
    logger.info(f"Hour range: {df['hour_moscow'].min()} - {df['hour_moscow'].max()}")
    
    return df

def format_timestamp(ts_sec: int) -> str:
    dt = datetime.fromtimestamp(ts_sec) + timedelta(hours=3)
    return dt.strftime("%Y-%m-%d %H:%M:%S")