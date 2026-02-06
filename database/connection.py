import os
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine


def get_database_url() -> str:
    """Get database URL from environment variable or default to SQLite."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Default to SQLite
    sqlite_path = os.getenv("SQLITE_PATH", "database.db")
    return f"sqlite:///{sqlite_path}"


def get_connect_args() -> dict:
    """Get connection arguments based on database type."""
    database_url = get_database_url()
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


database_url = get_database_url()
connect_args = get_connect_args()
engine = create_engine(database_url, connect_args=connect_args)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
