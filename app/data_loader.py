import pandas as pd
from .config import DATA_PATH
from .utils import compute_derived_fields
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_and_prepare_data() -> pd.DataFrame:
    logger.info(f"Loading data from {DATA_PATH}")

    try:
        df = pd.read_csv(DATA_PATH, low_memory=False)
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        raise
    
    logger.info(f"Initial dataframe shape: {df.shape}")
    logger.info(f"Columns: {df.columns.tolist()[:10]}...")

    if "_timestamp" not in df.columns:
        raise KeyError("_timestamp column not found in CSV")

    df["_timestamp"] = pd.to_numeric(df["_timestamp"], errors='coerce')

    initial_len = len(df)
    df = df.dropna(subset=["_timestamp"]).copy()
    if len(df) < initial_len:
        logger.warning(f"Removed {initial_len - len(df)} rows with invalid timestamps")

    numeric_cols = ['latitude', 'longitude', 'height', 'north_velocity', 'east_velocity', 
                    'up_velocity', 'roll', 'pitch', 'azimuth']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'pos_type__type' in df.columns:
        df['pos_type__type'] = pd.to_numeric(df['pos_type__type'], errors='coerce').fillna(0).astype(int)

    critical_cols = ['latitude', 'longitude', 'north_velocity', 'east_velocity']
    df = df.dropna(subset=critical_cols).copy()
    
    logger.info(f"After cleaning: {df.shape} rows")

    df = compute_derived_fields(df)
    
    return df