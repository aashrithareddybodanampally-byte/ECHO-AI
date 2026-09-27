from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str

class DatabaseHealthResponse(BaseModel):
    status: str
    database: str
