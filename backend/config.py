"""Change these defaults or set the matching environment variables for a new topic."""

import os
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SYSTEM_NAME = os.getenv("SYSTEM_NAME", "基于 YOLO 的安全帽佩戴检测系统")
SYSTEM_DESCRIPTION = os.getenv("SYSTEM_DESCRIPTION", "识别安全帽佩戴情况，查看未佩戴目标与历史检测记录。")
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(BASE_DIR / "models" / "best.pt"))).expanduser()
if not MODEL_PATH.is_absolute():
    MODEL_PATH = (BASE_DIR / MODEL_PATH).resolve()
ACTIVE_MODEL_FILE = BASE_DIR / "models" / "active.json"
try:
    ACTIVE_MODEL = json.loads(ACTIVE_MODEL_FILE.read_text(encoding="utf-8"))
except (FileNotFoundError, ValueError):
    ACTIVE_MODEL = {}
MODEL_NAME = os.getenv("MODEL_NAME", MODEL_PATH.stem if os.getenv("MODEL_PATH") else ACTIVE_MODEL.get("name", MODEL_PATH.stem))
MODEL_ID = os.getenv("MODEL_ID", MODEL_PATH.stem if os.getenv("MODEL_PATH") else ACTIVE_MODEL.get("id", MODEL_PATH.stem))
DEFAULT_CONF = float(os.getenv("DEFAULT_CONF", "0.25"))
UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "results"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "200"))
MAX_VIDEO_FRAMES = int(os.getenv("MAX_VIDEO_FRAMES", "18000"))

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "admin123"),
    "database": os.getenv("MYSQL_DATABASE", "yolo_template"),
    "charset": "utf8mb4",
    "connect_timeout": 5,
}
