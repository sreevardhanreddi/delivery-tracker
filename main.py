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
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from database.connection import create_db_and_tables, engine, get_session
from models.track_package import CreatePackage, TrackPackage
from services.telegram import send_message
from services.tracker import track_all
from services.tracking_service import update_package_tracking
from tasks.tracker import update_packages_status

import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi import APIRouter, Depends
from fastapi import Header, status


SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", 10))
# Load env (if using python-dotenv, load it before)
SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")

API_KEY = os.getenv("API_KEY", None)
# Config credentials (plain text)
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "password")
# Set up the scheduler
scheduler = AsyncIOScheduler()
# Add the job with proper configuration
scheduler.add_job(
    update_packages_status,
    "interval",
    seconds=SLEEP_INTERVAL,
    id="update_packages",
    replace_existing=True,
)


def verify_api_key(request: Request,x_api_key: str = Header(None)):
    """
    Dependency to secure API routes with a shared API key.
    Clients must include the header:
        X-API-Key: <your_key_here>
    """
    if request.session.get("user"):
        return
    
    if API_KEY is None:
        raise HTTPException(status_code=500, detail="API key not configured on server")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

# Ensure the scheduler shuts down properly on application exit.
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    # Start the scheduler when the app starts
    scheduler.start()
    yield
    # Shutdown the scheduler when the app stops
    scheduler.shutdown()


app = FastAPI(title="Indian Courier Tracking API", lifespan=lifespan)

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


logging.basicConfig(level=logging.INFO)


@app.get("/health",dependencies=[Depends(verify_api_key)])
def health():
    return {"status": "ok"}



@app.get("/api/track",dependencies=[Depends(verify_api_key)])
def list_packages(
    session: Session = Depends(get_session), offset: int = 0, limit: int = 100
):
    packages = session.exec(
        select(TrackPackage)
        .order_by(TrackPackage.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return packages


@app.post("/api/track", response_model=TrackPackage,dependencies=[Depends(verify_api_key)])
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
        events="[{'location': '', 'details': '', 'date_time': ''}]",
        status="Tracking in progress...",
    )
    session.add(package_obj)
    session.commit()
    session.refresh(package_obj)

    # Add the tracking task to background tasks
    background_tasks.add_task(update_package_tracking, package_obj.id, package.number)

    return package_obj


@app.delete("/api/track/{num}",dependencies=[Depends(verify_api_key)])
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

# --- Utility functions ---
def get_current_user(request: Request):
    return request.session.get("user")

def require_login(request: Request):
    """Redirects to /login if user not logged in."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return None

# --- Routes ---

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    # Already logged in
    if get_current_user(request):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == AUTH_USERNAME and password == AUTH_PASSWORD:
        request.session["user"] = username
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)

# --- Protect the main page ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect
    user = get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/dashboard")
def dashboard(request: Request):
    redirect = require_login(request)
    if redirect:
        return redirect
    user = get_current_user(request)
    return {"message": f"Welcome, {user}"}
