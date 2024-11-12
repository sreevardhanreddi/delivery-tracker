import json

from asyncer import asyncify
from loguru import logger
from sqlmodel import Session, select

from database.connection import engine
from models.track_package import TrackPackage
from services.telegram import send_message
from services.tracker import bd_track
from utils.common import dict_to_str


async def update_packages_status():
    logger.info("Running the task")
    with Session(engine) as session:
        packages = session.exec(select(TrackPackage)).all()
        for package in packages:
            status = bd_track(package.number)
            if status is None:
                continue
            logger.info(f"Package {package.number} status: {dict_to_str(status[0])}")
            if status[0]["details"] != package.status:
                package.events = json.dumps(status)
                package.status = status[0]["details"]
                session.add(package)
                session.commit()
                logger.info(
                    f"Package {package.number} updated to {dict_to_str(status[0])}"
                )
                await send_message(
                    f"Package {package.number} updated to {dict_to_str(status[0])}"
                )

            if str(status[0]["details"]) == "Shipment Delivered":
                logger.info(f"Package {package.number} delivered")
                await send_message(f"Package {package.number} delivered")
                logger.info(f"Deleting package {package.number}")
                session.delete(package)
                session.commit()
