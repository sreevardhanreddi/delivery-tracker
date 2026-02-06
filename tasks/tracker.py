from asyncer import asyncify
from loguru import logger
from sqlmodel import Session, select

from database.connection import engine
from models.track_package import TrackPackage
from models.tracking_event import TrackingEvent
from services.telegram import send_message
from services.tracker import bd_track, track_all, track_by_service
from utils.common import dict_to_str, parse_date_time_string


async def update_packages_status():
    logger.info("Running the task")
    with Session(engine) as session:
        packages = session.exec(
            select(TrackPackage).where(TrackPackage.status != "Delivered")
        ).all()
        for package in packages:
            status = track_by_service(package.number, package.service)
            events = status.get("events", None)
            if events is None:
                continue
            # logger.info(f"Package {package.number} status: {dict_to_str(events[0])}")
            logger.info(
                f"Package {package.number} {package.service} {package.description} updated to {dict_to_str(events[0])}"
            )
            # Check if the latest event has changed by comparing with DB
            latest_db_event = session.exec(
                select(TrackingEvent)
                .where(TrackingEvent.package_id == package.id)
                .order_by(TrackingEvent.date_time.desc())
            ).first()
            latest_event = events[0]
            latest_event_date_time = latest_event.get("date_time")
            if isinstance(latest_event_date_time, str):
                latest_event_date_time = parse_date_time_string(latest_event_date_time)
            has_changed = (
                not latest_db_event
                or latest_db_event.details != latest_event.get("details", "")
                or latest_db_event.date_time != latest_event_date_time
            )
            if has_changed:
                package.status = events[0]["details"]
                eta = status.get("eta", "")
                package.eta = eta.strftime("%Y-%m-%d %H:%M:%S") if eta else ""
                session.add(package)
                session.commit()

                # Update TrackingEvent table: insert only new events
                for event in events:
                    date_time = event.get("date_time")
                    if isinstance(date_time, str):
                        date_time = parse_date_time_string(date_time)
                    location = event.get("location", "")
                    details = event.get("details", "")
                    existing = session.exec(
                        select(TrackingEvent).where(
                            TrackingEvent.package_id == package.id,
                            TrackingEvent.date_time == date_time,
                            TrackingEvent.details == details,
                            TrackingEvent.location == location,
                        )
                    ).first()
                    if not existing:
                        tracking_event = TrackingEvent(
                            package_id=package.id,
                            location=location,
                            details=details,
                            date_time=date_time,
                        )
                        session.add(tracking_event)
                session.commit()

                logger.info(
                    f"Package {package.number} {package.service} {package.description} updated to {dict_to_str(events[0])}"
                )
                await send_message(
                    f"Package {package.number} {package.service} {package.description} updated to {dict_to_str(events[0])}"
                )

            if str(events[0]["details"]) in [
                "Shipment Delivered",
                "Successfully Delivered",
                "Delivered",
                "Shipment delivered",
                "Shipment has been delivered",
            ]:
                logger.info(f"Package {package.number} delivered")
                await send_message(f"Package {package.number} delivered")
                logger.info(f"Updating package status {package.number} to Delivered.")
                package.status = "Delivered"
                session.add(package)
                # session.delete(package)
                session.commit()
