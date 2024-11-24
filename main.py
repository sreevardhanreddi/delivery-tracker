import json
import logging
import os

from dotenv import load_dotenv
from loguru import logger

from utils.common import dict_to_str

load_dotenv()

from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Session, select

from database.connection import create_db_and_tables, get_session
from models.track_package import CreatePackage, TrackPackage
from services.telegram import send_message
from services.tracker import bd_track, dtdc_track, track_all
from tasks.tracker import update_packages_status

SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", 10))

# Set up the scheduler
scheduler = AsyncIOScheduler()
# every 1 minute
trigger = CronTrigger.from_crontab("*/1 * * * *")
scheduler.add_job(
    update_packages_status,
    "interval",
    seconds=SLEEP_INTERVAL,
)

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
    scheduler.start()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/track")
def list_packages(
    session: Session = Depends(get_session), offset: int = 0, limit: int = 10
):
    packages = session.exec(select(TrackPackage).offset(offset).limit(limit)).all()
    return packages


@app.post("/track", response_model=TrackPackage)
def create_package(
    package: CreatePackage,
    session: Session = Depends(get_session),
):

    if session.exec(
        select(TrackPackage).where(TrackPackage.number == package.number)
    ).first():
        raise HTTPException(status_code=400, detail="Package already exists")

    status, service = track_all(package.number)
    if status is None:
        raise HTTPException(status_code=404, detail="Package not found")

    json_events = ""
    if status:
        json_events = json.dumps(status)
    package_obj = TrackPackage(
        number=package.number,
        service=service or "",
        description=package.description,
        events=json_events,
        status=status[0]["details"],
    )
    session.add(package_obj)
    session.commit()
    session.refresh(package_obj)

    return package_obj


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
