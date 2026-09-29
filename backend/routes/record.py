"""History and protected media access by record ID."""

from flask import Blueprint, abort, jsonify, request, send_from_directory

from config import MODEL_ID, RESULT_DIR, UPLOAD_DIR
from db import connection, fetch_all, fetch_one
from services.helmet_policy import wearing_status


bp = Blueprint("record", __name__, url_prefix="/api/records")


def _serialize(row):
    if row is None:
        return None
    item = dict(row)
    item["created_at"] = item["created_at"].isoformat(sep=" ")
    item["original_url"] = f"/api/records/{item['id']}/media/original"
    item["result_url"] = f"/api/records/{item['id']}/media/result"
    item["status"] = "violation" if item.get("no_helmet_count", 0) else "compliant" if item.get("helmet_count", 0) else "unknown"
    item.pop("original_path", None)
    item.pop("result_path", None)
    return item


@bp.get("")
def list_records():
    try:
        page = max(1, int(request.args.get("page", 1)))
        page_size = min(50, max(1, int(request.args.get("page_size", 10))))
    except ValueError:
        return jsonify({"error": "分页参数无效。"}), 400
    kind = request.args.get("type", "")
    if kind not in ("", "image", "video"):
        return jsonify({"error": "检测类型无效。"}), 400
    where = "WHERE model_id = %s" + (" AND detect_type = %s" if kind else "")
    params = (MODEL_ID, kind) if kind else (MODEL_ID,)
    count = fetch_one(f"SELECT COUNT(*) AS total FROM detect_record {where}", params)["total"]
    rows = fetch_all(
        f"SELECT * FROM detect_record {where} ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s",
        params + (page_size, (page - 1) * page_size),
    )
    return jsonify({"items": [_serialize(row) for row in rows], "total": count,
                    "page": page, "page_size": page_size})


@bp.get("/<int:record_id>")
def get_record(record_id):
    row = fetch_one("SELECT * FROM detect_record WHERE id = %s", (record_id,))
    if not row:
        abort(404)
    if row["detect_type"] == "image":
        objects = fetch_all(
            "SELECT frame_index, class_id, class_name, confidence, x1, y1, x2, y2 "
            "FROM detect_object WHERE record_id = %s ORDER BY id", (record_id,))
        for item in objects:
            item["wearing_status"] = wearing_status(item["class_name"])
        extra = {"objects": objects}
    else:
        classes = fetch_all(
            "SELECT class_name, COUNT(*) AS count FROM detect_object "
            "WHERE record_id = %s GROUP BY class_name ORDER BY count DESC", (record_id,))
        for item in classes:
            item["wearing_status"] = wearing_status(item["class_name"])
        extra = {"classes": classes}
    return jsonify({**_serialize(row), **extra})


@bp.delete("/<int:record_id>")
def delete_record(record_id):
    with connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT original_path, result_path FROM detect_record WHERE id = %s", (record_id,))
            row = cursor.fetchone()
            if not row:
                abort(404)
            cursor.execute("DELETE FROM detect_record WHERE id = %s", (record_id,))
    (UPLOAD_DIR / row["original_path"]).unlink(missing_ok=True)
    (RESULT_DIR / row["result_path"]).unlink(missing_ok=True)
    return "", 204


@bp.get("/<int:record_id>/media/<kind>")
def media(record_id, kind):
    if kind not in ("original", "result"):
        abort(404)
    row = fetch_one("SELECT original_path, result_path FROM detect_record WHERE id = %s", (record_id,))
    if not row:
        abort(404)
    folder = UPLOAD_DIR if kind == "original" else RESULT_DIR
    name = row["original_path"] if kind == "original" else row["result_path"]
    return send_from_directory(folder, name, conditional=True)
