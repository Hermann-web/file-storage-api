# main.py
import mimetypes
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from .constants import UPLOAD_DIR

# Initialize mimetypes
mimetypes.init()


# Helper functions
def get_file_extension(filename: str) -> str:
    """Extract file extension from filename using pathlib"""
    return Path(filename).suffix.lower()


def get_content_type(filename: str) -> str:
    """Get MIME content type for file"""
    content_type, _ = mimetypes.guess_type(filename)
    if content_type is None:
        # Default content types for common file extensions
        ext = get_file_extension(filename)
        content_type_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".json": "application/json",
            ".zip": "application/zip",
        }
        return content_type_map.get(ext, "application/octet-stream")
    return content_type


async def save_file_to_disk(file: UploadFile, private_filename: str) -> int:
    """Save uploaded file with private filename using pathlib and return file size"""
    file_path = UPLOAD_DIR / private_filename

    file_size = 0
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        file_size = len(content)
        await f.write(content)

    return file_size
