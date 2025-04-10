from datetime import datetime
from typing import Annotated, Dict, List, Optional

from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select
from models.tracking_event import TrackingEvents


# Define the model
class TrackPackage(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    number: str = Field(unique=True)
    service: str = Field(default="")
    description: str = Field(default="")
    events: str = Field(default="[]")  # Stored as JSON string
    status: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)



class CreatePackage(BaseModel):
    number: str
    description: str
