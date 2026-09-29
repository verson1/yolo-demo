"""Flask API entry point: python app.py"""

import logging

import pymysql
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from config import DEFAULT_CONF, MAX_UPLOAD_MB, MODEL_ID, MODEL_NAME, RESULT_DIR, SYSTEM_DESCRIPTION, SYSTEM_NAME, UPLOAD_DIR
from routes.dashboard import bp as dashboard_bp
from routes.detect import bp as detect_bp
from routes.record import bp as record_bp
from services.yolo_service import DetectionError, yolo_service


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    app.register_blueprint(detect_bp)
    app.register_blueprint(record_bp)
    app.register_blueprint(dashboard_bp)

    @app.get("/api/model/info")
    def model_info():
        payload = {"system_name": SYSTEM_NAME, "description": SYSTEM_DESCRIPTION,
                   "model_id": MODEL_ID,
                   "default_confidence": DEFAULT_CONF}
        try:
            payload.update(yolo_service.info())
            payload["name"] = MODEL_NAME
            payload["ready"] = True
        except DetectionError as exc:
            payload.update({"name": MODEL_NAME, "path": str(yolo_service.model_path),
                            "classes": [], "ready": False, "message": str(exc)})
        return jsonify(payload)

    @app.errorhandler(DetectionError)
    def detection_error(exc):
        return jsonify({"error": str(exc)}), 400

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_exc):
        return jsonify({"error": f"文件超过 {MAX_UPLOAD_MB} MB 的上传上限。"}), 413

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify({"error": exc.description}), exc.code

    @app.errorhandler(pymysql.MySQLError)
    def database_error(exc):
        app.logger.error("Database error: %s", exc)
        return jsonify({"error": "数据库不可用，请检查 MySQL 连接和 schema.sql。"}), 503

    @app.errorhandler(Exception)
    def internal_error(exc):
        app.logger.exception("Unexpected error: %s", exc)
        return jsonify({"error": "服务处理失败，请查看后端日志。"}), 500

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_app().run(host="127.0.0.1", port=5000, debug=True)
