from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.tracking_event import TrackingEvent


class TrackPackage(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    number: str = Field(unique=True)
    service: str = Field(default="")
    description: str = Field(default="")
    eta: str = Field(default="")
    status: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    tracking_events: List["TrackingEvent"] = Relationship(back_populates="package")


class CreatePackage(BaseModel):
    number: str
    description: str


class TrackingEventRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    package_id: int
    location: str
    details: str
    date_time: datetime
    created_at: datetime


class TrackPackageRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    number: str
    service: str
    description: str
    eta: str
    status: str
    created_at: datetime
    updated_at: datetime
    tracking_events: List[TrackingEventRead] = []
