# main.py
import os
import time
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import EmailStr
from slugify import slugify
from sqlalchemy import text

from .constants import UPLOAD_DIR
from .db import FileRecord, FileUploadResponse, SessionLocal
from .logging_config import log_error, log_info, log_warn
from .utils import get_content_type, get_file_extension, save_file_to_disk

# Load environment variables from a .env file (if it exists)
load_dotenv()


# Get CORS origins from environment variable, default to allow all
ALLOWED_ORIGINS_RAW = os.getenv("ALLOWED_ORIGINS", "*")

if ALLOWED_ORIGINS_RAW != "*":
    # Split comma-separated origins and strip whitespace
    ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS_RAW.split(",")]
else:
    ALLOWED_ORIGINS = []  # Empty list can be interpreted as "allow all" depending on your CORS setup


# FastAPI app
app = FastAPI(title="Simple File Storage API", version="1.0.0")

# CORS middleware with environment configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log request start
    log_info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log successful response
        log_info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
            client_ip=request.client.host if request.client else None,
        )

        return response
    except Exception as e:
        process_time = time.time() - start_time

        # Log error
        log_error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time_ms=round(process_time * 1000, 2),
            client_ip=request.client.host if request.client else None,
        )
        raise


# API Routes
@app.post("/api/upload", response_model=FileUploadResponse)
async def upload_file(
    email: EmailStr = Form(...), label: str = Form(...), file: UploadFile = File(...)
):
    """
    Upload a single file with email and label.
    Returns public URL for downloading the file.
    """
    log_info(
        "File upload started",
        email=email,
        label=label,
        filename=file.filename,
        content_type=file.content_type,
    )

    db = SessionLocal()
    try:
        # Validate file
        if not file.filename:
            log_warn("Upload failed: no filename provided", email=email)
            raise HTTPException(status_code=400, detail="File must have a filename")

        # Generate UUIDs
        public_id = str(uuid.uuid4())
        private_id = str(uuid.uuid4())

        log_info(
            "Generated file IDs",
            email=email,
            filename=file.filename,
            public_id=public_id,
            private_id=private_id,
        )

        # Get file extension and content type using pathlib
        file_extension = get_file_extension(file.filename)
        if not file_extension:
            log_warn(
                "Upload failed: no file extension", email=email, filename=file.filename
            )
            raise HTTPException(status_code=400, detail="File must have an extension")

        content_type = get_content_type(file.filename)

        # Create private filename with extension
        private_filename = f"{private_id}{file_extension}"

        # Save file to disk and get file size
        file_size = await save_file_to_disk(file, private_filename)

        log_info(
            "File saved to disk",
            email=email,
            filename=file.filename,
            private_filename=private_filename,
            file_size=file_size,
        )

        # Save record to database
        file_record = FileRecord(
            public_id=public_id,
            private_id=private_id,
            email=email,
            label=label,
            original_filename=file.filename,
            file_extension=file_extension,
            content_type=content_type,
            file_size=str(file_size),
        )

        db.add(file_record)
        db.commit()

        # Generate public URL
        public_url = f"/download/{public_id}"

        log_info(
            "File upload completed successfully",
            email=email,
            filename=file.filename,
            public_id=public_id,
            public_url=public_url,
            file_size=file_size,
        )

        return FileUploadResponse(
            success=True,
            public_url=public_url,
            message=f"File '{file.filename}' uploaded successfully ({file_size:,} bytes)",
        )

    except HTTPException as e:
        log_warn(
            "Upload failed with HTTP exception",
            email=email,
            filename=file.filename,
            status_code=e.status_code,
            detail=e.detail,
        )
        raise
    except Exception as e:
        db.rollback()
        log_error(
            "Upload failed with unexpected error",
            email=email,
            filename=file.filename,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        db.close()


@app.get("/download/{public_id}")
async def download_file(public_id: str):
    """Download file using public ID with proper pathlib handling"""
    log_info("File download requested", public_id=public_id)

    db = SessionLocal()
    try:
        # Find file record
        file_record = (
            db.query(FileRecord).filter(FileRecord.public_id == public_id).first()
        )
        if not file_record:
            log_warn("Download failed: file record not found", public_id=public_id)
            raise HTTPException(status_code=404, detail="File not found")

        # Construct private filename and file path using pathlib
        private_filename = f"{file_record.private_id}{file_record.file_extension}"
        file_path = UPLOAD_DIR / private_filename

        log_info(
            "File record found",
            public_id=public_id,
            private_filename=private_filename,
            original_filename=file_record.original_filename,
            email=file_record.email,
        )

        # Check if file exists on disk using pathlib
        if not file_path.exists():
            log_error(
                "Download failed: file not found on disk",
                public_id=public_id,
                private_filename=private_filename,
                file_path=str(file_path),
            )
            raise HTTPException(status_code=404, detail="File not found on disk")

        # Verify file is actually a file (not directory)
        if not file_path.is_file():
            log_error(
                "Download failed: path is not a file",
                public_id=public_id,
                private_filename=private_filename,
                file_path=str(file_path),
            )
            raise HTTPException(status_code=404, detail="Path is not a file")

        log_info(
            "File download completed successfully",
            public_id=public_id,
            original_filename=file_record.original_filename,
            file_size=file_record.file_size,
            email=file_record.email,
        )

        fname: str = slugify(file_record.original_filename)

        return FileResponse(
            path=str(file_path),  # Convert pathlib Path to string for FileResponse
            filename=fname,
            media_type=file_record.content_type,
            headers={
                "Content-Length": file_record.file_size,
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Disposition": f'attachment; filename="{fname}"',
            },
        )

    except HTTPException as e:
        log_warn(
            "Download failed with HTTP exception",
            public_id=public_id,
            status_code=e.status_code,
            detail=e.detail,
        )
        raise
    except Exception as e:
        log_error(
            "Download failed with unexpected error", public_id=public_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
    finally:
        db.close()


@app.get("/api/file-info/{public_id}")
async def get_file_info(public_id: str):
    """Get file metadata without downloading the file"""
    log_info("File info requested", public_id=public_id)

    db = SessionLocal()
    try:
        file_record = (
            db.query(FileRecord).filter(FileRecord.public_id == public_id).first()
        )
        if not file_record:
            log_warn("File info failed: file record not found", public_id=public_id)
            raise HTTPException(status_code=404, detail="File not found")

        # Check if physical file still exists
        private_filename = f"{file_record.private_id}{file_record.file_extension}"
        file_path = UPLOAD_DIR / private_filename
        file_exists = file_path.exists() and file_path.is_file()

        log_info(
            "File info retrieved successfully",
            public_id=public_id,
            original_filename=file_record.original_filename,
            email=file_record.email,
            file_exists_on_disk=file_exists,
        )

        return {
            "public_id": file_record.public_id,
            "email": file_record.email,
            "label": file_record.label,
            "original_filename": file_record.original_filename,
            "content_type": file_record.content_type,
            "file_size": file_record.file_size,
            "created_at": file_record.created_at,
            "file_exists_on_disk": file_exists,
        }

    except HTTPException as e:
        log_warn(
            "File info failed with HTTP exception",
            public_id=public_id,
            status_code=e.status_code,
            detail=e.detail,
        )
        raise
    except Exception as e:
        log_error(
            "File info failed with unexpected error", public_id=public_id, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"File info retrieval failed: {str(e)}"
        )
    finally:
        db.close()


@app.delete("/api/file/{public_id}")
async def delete_file(public_id: str):
    """Delete a file and its database record"""
    log_info("File deletion requested", public_id=public_id)

    db = SessionLocal()
    try:
        file_record = (
            db.query(FileRecord).filter(FileRecord.public_id == public_id).first()
        )
        if not file_record:
            log_warn("Delete failed: file record not found", public_id=public_id)
            raise HTTPException(status_code=404, detail="File not found")

        # Delete physical file using pathlib
        private_filename = f"{file_record.private_id}{file_record.file_extension}"
        file_path = UPLOAD_DIR / private_filename

        file_existed = False
        if file_path.exists():
            file_path.unlink()  # pathlib method to delete file
            file_existed = True
            log_info(
                "Physical file deleted",
                public_id=public_id,
                private_filename=private_filename,
            )
        else:
            log_warn(
                "Physical file not found during deletion",
                public_id=public_id,
                private_filename=private_filename,
            )

        # Delete database record
        db.delete(file_record)
        db.commit()

        log_info(
            "File deletion completed successfully",
            public_id=public_id,
            original_filename=file_record.original_filename,
            email=file_record.email,
            physical_file_existed=file_existed,
        )

        return {
            "success": True,
            "message": f"File '{file_record.original_filename}' deleted successfully",
        }

    except HTTPException as e:
        log_warn(
            "Delete failed with HTTP exception",
            public_id=public_id,
            status_code=e.status_code,
            detail=e.detail,
        )
        raise
    except Exception as e:
        db.rollback()
        log_error(
            "Delete failed with unexpected error", public_id=public_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
    finally:
        db.close()


@app.get("/")
async def root():
    log_info("Root endpoint accessed")

    return {
        "message": "Simple File Storage API",
        "version": "1.0.0",
        "upload_dir": str(UPLOAD_DIR.absolute()),
        "upload_dir_exists": UPLOAD_DIR.exists(),
        "cors_origins": ALLOWED_ORIGINS,
    }


@app.get("/health")
async def health():
    """Health check endpoint with storage info"""
    log_info("Health check requested")

    try:
        # Check database connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))  # wrap in text()
        db.close()
        db_healthy = True
        log_info("Database health check passed")
    except Exception as e:
        db_healthy = False
        log_error("Database health check failed", error=str(e))

    health_status = {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "upload_directory": {
            "path": str(UPLOAD_DIR.absolute()),
            "exists": UPLOAD_DIR.exists(),
            "is_dir": UPLOAD_DIR.is_dir() if UPLOAD_DIR.exists() else False,
        },
        "cors_origins": ALLOWED_ORIGINS,
    }

    log_info(
        "Health check completed",
        status=health_status["status"],
        database_status=health_status["database"],
        upload_dir_exists=health_status["upload_directory"]["exists"],
    )

    return health_status


# Application startup event
@app.on_event("startup")
async def startup_event():
    log_info(
        "Application starting up",
        upload_dir=str(UPLOAD_DIR.absolute()),
        upload_dir_exists=UPLOAD_DIR.exists(),
        cors_origins=ALLOWED_ORIGINS,
    )


# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    log_info("Application shutting down")
