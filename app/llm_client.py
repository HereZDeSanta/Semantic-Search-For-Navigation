import httpx
import json
import logging
import asyncio
from .config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def call_llm(prompt: str, retry_count: int = 3) -> str:
    
    
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is not set")
        return '{"type": "unknown"}'
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Semantic Search Engine"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 300
        }
        
        last_error = None
        
        for attempt in range(retry_count):
            try:
                logger.info(f"LLM request attempt {attempt + 1}/{retry_count}")
                
                response = await client.post(
                    OPENROUTER_BASE_URL, 
                    headers=headers, 
                    json=payload
                )
                
                # Обработка ошибок
                if response.status_code == 429:
                    wait_time = 2 ** attempt 
                    logger.warning(f"Rate limited (429). Retrying in {wait_time} seconds... (attempt {attempt + 1}/{retry_count})")
                    await asyncio.sleep(wait_time)
                    continue
                
                if response.status_code == 401:
                    logger.error("Authentication failed (401). Check your API key")
                    return '{"type": "unknown"}'
                
                if response.status_code == 402:
                    logger.error("Payment required (402). Insufficient credits")
                    return '{"type": "unknown"}'
                
                if response.status_code == 403:
                    logger.error("Forbidden (403). Access denied")
                    return '{"type": "unknown"}'
                
                if response.status_code != 200:
                    logger.error(f"HTTP error {response.status_code}: {response.text[:200]}")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(1)
                        continue
                    return '{"type": "unknown"}'

                content_type = response.headers.get("content-type", "")
                if "application/json" not in content_type:
                    logger.error(f"Non-JSON response (Content-Type: {content_type})")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(1)
                        continue
                    return '{"type": "unknown"}'

                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.error(f"Raw response: {response.text[:200]}")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(1)
                        continue
                    return '{"type": "unknown"}'

                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"LLM response received successfully ({len(content)} chars)")
                    return content
                
                if "error" in data:
                    logger.error(f"OpenRouter API error: {data['error']}")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(1)
                        continue
                    return '{"type": "unknown"}'
                
                logger.error(f"Unexpected response structure: {data.keys()}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(1)
                    continue
                return '{"type": "unknown"}'
                
            except httpx.TimeoutException as e:
                last_error = f"Timeout: {e}"
                logger.error(f"Request timeout (attempt {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                    
            except httpx.ConnectError as e:
                last_error = f"Connection error: {e}"
                logger.error(f"Connection error (attempt {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2)
                    continue
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Unexpected error (attempt {attempt + 1}/{retry_count}): {e}", exc_info=True)
                if attempt < retry_count - 1:
                    await asyncio.sleep(1)
                    continue
        
        logger.error(f"All {retry_count} attempts failed. Last error: {last_error}")
        return '{"type": "unknown"}'