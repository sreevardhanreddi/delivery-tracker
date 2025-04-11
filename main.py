import logging
import os

from dotenv import load_dotenv
from loguru import logger

from utils.common import dict_to_str, json_dumps

load_dotenv()

from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import Depends, FastAPI, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from database.connection import create_db_and_tables, get_session, engine
from models.track_package import CreatePackage, TrackPackage
from services.telegram import send_message
from services.tracker import track_all
from tasks.tracker import update_packages_status
from services.tracking_service import update_package_tracking

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

# Ensure the scheduler shuts down properly on application exit.
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    scheduler.shutdown()

app = FastAPI(title="Indian Courier Tracking API", lifespan=lifespan)

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

logging.basicConfig(level=logging.INFO)

@app.on_event("startup")
async def on_startup():
    create_db_and_tables()
    scheduler.start()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/track")
def list_packages(
    session: Session = Depends(get_session), offset: int = 0, limit: int = 10
):
    packages = session.exec(select(TrackPackage).offset(offset).limit(limit)).all()
    return packages


@app.post("/api/track", response_model=TrackPackage)
async def create_package(
    package: CreatePackage,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    if session.exec(
        select(TrackPackage).where(TrackPackage.number == package.number)
    ).first():
        raise HTTPException(status_code=400, detail="Package already exists")

    # Create a temporary package object
    package_obj = TrackPackage(
        number=package.number,
        service="",
        description=package.description,
        events="[]",
        status="Tracking in progress...",
    )
    session.add(package_obj)
    session.commit()
    session.refresh(package_obj)

    # Add the tracking task to background tasks
    background_tasks.add_task(update_package_tracking, package_obj.id, package.number)
    
    return package_obj


@app.delete("/api/track/{num}")
def delete_package(num: str, session: Session = Depends(get_session)):
    package = session.exec(
        select(TrackPackage).where(TrackPackage.number == num)
    ).first()
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")

    else:
        session.delete(package)
        session.commit()
    return {"success": True, "message": "Package deleted"}
