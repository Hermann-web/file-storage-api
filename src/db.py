# main.py
from datetime import datetime

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, DateTime, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.sql import func

from .constants import SQLALCHEMY_DATABASE_URL

# Database setup
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Pydantic Models
class FileUploadResponse(BaseModel):
    success: bool
    public_url: str
    public_id: str
    message: str


# SQLAlchemy Model
class FileRecord(Base):
    __tablename__ = "files"

    public_id: Mapped[str] = mapped_column(
        String, primary_key=True, index=True
    )  # UUID for public access
    private_id: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )  # UUID for server filename
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    label: Mapped[str] = mapped_column(
        String, nullable=False
    )  # e.g., "s5Transcripts", "resume", etc.
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_extension: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)  # MIME type
    file_size: Mapped[str] = mapped_column(String, nullable=False)  # File size in bytes
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# Create tables
Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
