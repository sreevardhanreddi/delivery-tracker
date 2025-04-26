from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TrackingEvent(BaseModel):
    """
    Schema for a single tracking event in a package's journey.
    """

    location: str = Field(..., description="Location where the event occurred")
    details: str = Field(..., description="Description of the event")
    date_time: datetime = Field(
        ..., description="Date and time when the event occurred"
    )


class TrackingEvents(BaseModel):
    """
    Schema for a collection of tracking events.
    """

    events: List[TrackingEvent] = Field(
        default_factory=list, description="List of tracking events"
    )
