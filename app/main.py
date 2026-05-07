from fastapi import FastAPI, HTTPException
from .models import QueryRequest, GenericResponse
from .data_loader import load_and_prepare_data
from .query_parser import parse_query
from .query_executor import (
    execute_aggregation,
    execute_bad_position,
    execute_time_slice,
    execute_braking_events,
    execute_geo_filter
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Semantic Search Engine for Navigation Data")

# Загружаем данные при старте
logger.info("Loading data...")
df = load_and_prepare_data()
logger.info(f"Data loaded successfully. Shape: {df.shape}")

@app.get("/")
async def root():
    return {
        "message": "Semantic Search Engine for Navigation Data",
        "data_shape": df.shape,
        "available_endpoints": {
            "POST /query": "Send natural language query"
        }
    }

@app.post("/query", response_model=GenericResponse)
async def handle_query(req: QueryRequest):
    user_query = req.query
    logger.info(f"Processing query: {user_query}")
    
    parsed = await parse_query(user_query)
    qtype = parsed.get("type")
    logger.info(f"Parsed type: {qtype}, params: {parsed}")
    
    if qtype == "aggregation":
        metric = parsed.get("metric", "max_speed")
        result = execute_aggregation(df, metric)
    elif qtype == "filter_bad_position":
        result = execute_bad_position(df)
    elif qtype == "time_slice":
        start = parsed.get("start_hour", 16)
        end = parsed.get("end_hour", 19)
        result = execute_time_slice(df, start, end)
    elif qtype == "braking_events":
        threshold = parsed.get("threshold", -2.0)
        result = execute_braking_events(df, threshold)
    elif qtype == "geo_filter":
        result = execute_geo_filter(
            df,
            parsed.get("min_lat", 55.5), 
            parsed.get("max_lat", 60.0),
            parsed.get("min_lon", 30.0), 
            parsed.get("max_lon", 37.5)
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported query type: {qtype}")
    
    return GenericResponse(status="success", query=user_query, result=result)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)