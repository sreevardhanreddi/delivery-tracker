from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.track_package import TrackPackage


class TrackingEvent(SQLModel, table=True):
    """Database model for a single tracking event in a package's journey."""

    id: int = Field(default=None, primary_key=True)
    package_id: int = Field(foreign_key="trackpackage.id", index=True)
    location: str = Field(default="")
    details: str = Field(default="")
    date_time: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)

    package: Optional["TrackPackage"] = Relationship(back_populates="tracking_events")


class TrackingEventCreate(BaseModel):
    """Schema for creating a tracking event."""

    location: str
    details: str
    date_time: datetime


class TrackingEventResponse(BaseModel):
    """Schema for tracking event API response."""

    id: int
    package_id: int
    location: str
    details: str
    date_time: datetime
