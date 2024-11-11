from datetime import datetime
from typing import Annotated, Dict, List

from sqlmodel import Field, Session, SQLModel, create_engine, select


# Define the model
class TrackPackage(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    number: str = Field(unique=True)
    description: str
    events: str
    status: str
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
