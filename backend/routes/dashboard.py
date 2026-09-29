"""Aggregate queries for the dashboard."""

from flask import Blueprint, jsonify

from config import MODEL_ID
from db import fetch_all, fetch_one
from services.helmet_policy import wearing_status


bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@bp.get("/summary")
def summary():
    data = fetch_one(
        """SELECT COUNT(*) AS total_records,
                  COALESCE(SUM(DATE(created_at) = CURDATE()), 0) AS today_records,
                  COALESCE(SUM(total_objects), 0) AS total_objects,
                  COALESCE(SUM(helmet_count), 0) AS helmet_count,
                  COALESCE(SUM(no_helmet_count), 0) AS no_helmet_count,
                  COALESCE(SUM(no_helmet_count > 0), 0) AS violation_records,
                  COALESCE(SUM(detect_type = 'image'), 0) AS image_records,
                  COALESCE(SUM(detect_type = 'video'), 0) AS video_records
           FROM detect_record WHERE model_id = %s""", (MODEL_ID,))
    recent = fetch_all(
        "SELECT id, detect_type, total_objects, helmet_count, no_helmet_count, elapsed_ms, created_at "
        "FROM detect_record WHERE model_id = %s ORDER BY created_at DESC, id DESC LIMIT 5", (MODEL_ID,))
    for row in recent:
        row["created_at"] = row["created_at"].isoformat(sep=" ")
    return jsonify({**data, "recent": recent})


@bp.get("/classes")
def classes():
    rows = fetch_all(
        "SELECT o.class_name AS name, COUNT(*) AS value FROM detect_object o "
        "JOIN detect_record r ON o.record_id = r.id WHERE r.model_id = %s "
        "GROUP BY o.class_name ORDER BY value DESC", (MODEL_ID,))
    for row in rows:
        row["wearing_status"] = wearing_status(row["name"])
    return jsonify(rows)


@bp.get("/trend")
def trend():
    return jsonify(fetch_all(
        """SELECT DATE_FORMAT(created_at, '%%Y-%%m-%%d') AS day,
                  COUNT(*) AS records,
                  COALESCE(SUM(no_helmet_count > 0), 0) AS violations
           FROM detect_record WHERE model_id = %s AND created_at >= CURDATE() - INTERVAL 6 DAY
           GROUP BY DATE(created_at) ORDER BY day""", (MODEL_ID,)))
