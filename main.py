import json
import logging

from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import (
    CronTrigger,
)  # allows us to specify a recurring time for execution
from fastapi import Depends, FastAPI, HTTPException, Query
from loguru import logger
from sqlmodel import Session, select

from database.connection import create_db_and_tables, get_session
from models.track_package import TrackPackage
from services.telegram import send_message
from services.tracker import bd_track
from tasks.tracker import update_packages_status

# Set up the scheduler
scheduler = AsyncIOScheduler()
# every 10 minutes
trigger = CronTrigger.from_crontab("*/1 * * * *")
scheduler.add_job(update_packages_status, trigger)
scheduler.start()

app = FastAPI()


# Ensure the scheduler shuts down properly on application exit.
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    scheduler.shutdown()


logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Bluedart Tracking API",
)


@app.on_event("startup")
async def on_startup():
    create_db_and_tables()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/track/{num}")
async def track_package(num: str, session: Session = Depends(get_session)):

    status = bd_track(num)
    if status is None:
        raise HTTPException(status_code=404, detail="Package not found")

    package = session.exec(
        select(TrackPackage).where(TrackPackage.number == num)
    ).first()

    if package:
        package.events = json.dumps(status)
        package.status = status[0]["details"]
        session.add(package)
        session.commit()

    else:
        package = TrackPackage(
            number=num,
            description="Bluedart",
            events=json.dumps(status),
            status=status[0]["details"],
        )
        session.add(package)
        session.commit()

    await send_message(f"Package {num} updated to {status[0]['details']}")

    return status


@app.get("/track")
def list_packages(
    session: Session = Depends(get_session), offset: int = 0, limit: int = 10
):
    packages = session.exec(select(TrackPackage).offset(offset).limit(limit)).all()
    return packages


@app.post("/track")
def create_package(
    num: str = Query(...),
    session: Session = Depends(get_session),
):

    if session.exec(select(TrackPackage).where(TrackPackage.number == num)).first():
        raise HTTPException(status_code=400, detail="Package already exists")

    status = bd_track(num)
    if status is None:
        raise HTTPException(status_code=404, detail="Package not found")

    json_events = ""
    if status:
        json_events = json.dumps(status)
    package = TrackPackage(
        number=num,
        description="Bluedart",
        events=json_events,
        status=status[0]["details"],
    )
    session.add(package)
    session.commit()

    return package


@app.delete("/track/{num}")
def delete_package(num: str, session: Session = Depends(get_session)):
    package = session.exec(
        select(TrackPackage).where(TrackPackage.number == num)
    ).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")

    else:
        session.delete(package)
        session.commit()
    return {"message": "Package deleted"}
