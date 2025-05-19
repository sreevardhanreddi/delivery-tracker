import json

from asyncer import asyncify
from loguru import logger
from sqlmodel import Session, select

from database.connection import engine
from models.track_package import TrackPackage
from services.telegram import send_message
from services.tracker import bd_track, track_all, track_by_service
from utils.common import dict_to_str, json_dumps


async def update_packages_status():
    logger.info("Running the task")
    with Session(engine) as session:
        packages = session.exec(
            select(TrackPackage).where(TrackPackage.status != "Delivered")
        ).all()
        for package in packages:
            status = track_by_service(package.number, package.service)
            events = status.get("events", None)
            if events is None or len(events) == 0:
                continue
            # logger.info(f"Package {package.number} status: {dict_to_str(events[0])}")
            logger.info(
                f"Package {package.number} {package.service} {package.description} updated to {dict_to_str(events[0])}"
            )
            if json.loads(json_dumps(events[0])) != json.loads(package.events)[0]:
                package.events = json_dumps(events)
                package.status = events[0]["details"]
                session.add(package)
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
