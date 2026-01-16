from asyncer import asyncify
from sqlmodel import Session, select

from database.connection import engine
from models.track_package import TrackPackage
from services.telegram import send_message
from services.tracker import track_all
from utils.common import dict_to_str, json_dumps


async def update_package_tracking(package_id: int, tracking_number: str):
    """Update package tracking information in the background."""
    # Run the synchronous track_all function in a separate thread
    status = await asyncify(track_all)(tracking_number)

    with Session(engine) as session:
        package = session.get(TrackPackage, package_id)
        if not package:
            return

        events = status.get("events", None)

        if events is None:
            package.status = "Package not found"
            session.add(package)
            session.commit()
            return

        json_events = json_dumps(events)
        package.service = status.get("service", "")
        package.events = json_events
        package.status = events[0]["details"]
        eta = status.get("eta", "")
        package.eta = eta.strftime("%Y-%m-%d %H:%M:%S") if eta else ""
        session.add(package)
        session.commit()

        msg = f"Package {package.number} {package.service} {package.description} updated to {dict_to_str(events[0])}"
        if package.eta:
            msg += f"\nETA: {package.eta}"

        await send_message(msg)
