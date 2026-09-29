"""Upload and inference endpoints."""

from pathlib import Path
from uuid import uuid4

from flask import Blueprint, jsonify, request

from config import DEFAULT_CONF, MODEL_ID, RESULT_DIR, UPLOAD_DIR
from db import connection
from services.helmet_policy import summarize
from services.yolo_service import DetectionError, yolo_service


bp = Blueprint("detect", __name__, url_prefix="/api")
ALLOWED = {"image": {".jpg", ".jpeg", ".png", ".webp"},
           "video": {".mp4", ".avi", ".mov", ".mkv"}}


def _confidence():
    try:
        value = float(request.form.get("confidence", DEFAULT_CONF))
    except (TypeError, ValueError):
        raise DetectionError("置信度必须是 0 到 1 之间的数字。") from None
    if not 0 < value <= 1:
        raise DetectionError("置信度必须大于 0 且不超过 1。")
    return value


def _run(kind):
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        raise DetectionError("请选择文件。")
    extension = Path(upload.filename).suffix.lower()
    if extension not in ALLOWED[kind]:
        raise DetectionError(f"不支持该文件格式。可用格式：{', '.join(sorted(ALLOWED[kind]))}")
    confidence = _confidence()
    identifier = uuid4().hex
    source = UPLOAD_DIR / f"{identifier}{extension}"
    destination = RESULT_DIR / f"{identifier}.{'jpg' if kind == 'image' else 'mp4'}"
    try:
        upload.save(source)
        if kind == "image":
            objects, elapsed_ms = yolo_service.image(source, destination, confidence)
            frames = None
        else:
            objects, elapsed_ms, frames = yolo_service.video(source, destination, confidence)
        counts = summarize(objects, is_video=kind == "video")
        with connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO detect_record
                       (detect_type, model_id, original_path, result_path, total_objects,
                        helmet_count, no_helmet_count, violation_frames, elapsed_ms, confidence)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (kind, MODEL_ID, source.name, destination.name, len(objects),
                     counts["helmet_count"], counts["no_helmet_count"], counts["violation_frames"],
                     elapsed_ms, confidence),
                )
                record_id = cursor.lastrowid
                if objects:
                    cursor.executemany(
                        """INSERT INTO detect_object
                           (record_id, frame_index, class_id, class_name, confidence, x1, y1, x2, y2)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        [(record_id, obj["frame_index"], obj["class_id"], obj["class_name"],
                          obj["confidence"], obj["x1"], obj["y1"], obj["x2"], obj["y2"])
                         for obj in objects],
                    )
        payload = {
            "id": record_id, "detect_type": kind, "total_objects": len(objects),
            "model_id": MODEL_ID, **counts,
            "elapsed_ms": elapsed_ms, "confidence": confidence,
            "original_url": f"/api/records/{record_id}/media/original",
            "result_url": f"/api/records/{record_id}/media/result",
            "objects": objects if kind == "image" else [],
        }
        if frames is not None:
            payload["frames"] = frames
        return jsonify(payload), 201
    except Exception:
        source.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise


@bp.post("/detect/image")
def detect_image():
    return _run("image")


@bp.post("/detect/video")
def detect_video():
    return _run("video")
