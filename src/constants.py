from pathlib import Path

PROJECT_FOLDER = Path(__file__).resolve().parent.parent

LOG_FOLDER = PROJECT_FOLDER / "logs"
LOG_FOLDER.mkdir(exist_ok=True)
LOG_FILE = LOG_FOLDER / "app.log"

# File storage directory using pathlib
UPLOAD_DIR = PROJECT_FOLDER / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


SQLALCHEMY_DATABASE_URL = "sqlite:///./files.db"
