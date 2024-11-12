import os

from fastapi import Security
from fastapi.exceptions import HTTPException
from fastapi.security import api_key

API_KEY = os.getenv("API_KEY", "")


api_key_header = api_key.APIKeyHeader(name="X-API-Key")


def validate_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized - API Key is invalid")
    return None
