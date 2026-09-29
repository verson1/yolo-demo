"""The only module coupled to Ultralytics; replace it to support another detector."""

import threading
import time
import subprocess
import os
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(__file__).resolve().parents[2] / ".ultralytics"))

from ultralytics import YOLO

from config import MAX_VIDEO_FRAMES, MODEL_NAME, MODEL_PATH
from services.helmet_policy import helmet_class_ids, wearing_status


class DetectionError(ValueError):
    pass


class YOLOService:
    def __init__(self, model_path=MODEL_PATH):
        self.model_path = model_path
        self._model = None
        self._class_ids = None
        self._lock = threading.RLock()

    def _get_model(self):
        if self._model is None:
            if not self.model_path.is_file():
                raise DetectionError(f"模型文件不存在：{self.model_path}。请先训练并复制 best.pt。")
            self._model = YOLO(str(self.model_path))
            if self._model.task != "detect":
                raise DetectionError("当前模板只支持目标检测权重，请使用 detect 任务训练的模型。")
            try:
                self._class_ids = helmet_class_ids(self._model.names)
            except ValueError as exc:
                self._model = None
                raise DetectionError(str(exc)) from exc
        return self._model

    def info(self):
        with self._lock:
            model = self._get_model()
            names = model.names
            classes = [{"id": int(key), "name": str(value)} for key, value in names.items()]
            return {"name": MODEL_NAME, "path": str(self.model_path), "classes": classes,
                    "helmet_class_ids": self._class_ids}

    @staticmethod
    def _objects(result, frame_index=None):
        names = result.names
        objects = []
        for box in result.boxes:
            class_id = int(box.cls.item())
            x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
            objects.append({
                "frame_index": frame_index,
                "class_id": class_id,
                "class_name": str(names[class_id]),
                "wearing_status": wearing_status(names[class_id]),
                "confidence": round(float(box.conf.item()), 4),
                "x1": round(x1, 2), "y1": round(y1, 2),
                "x2": round(x2, 2), "y2": round(y2, 2),
            })
        return objects

    def image(self, source, destination, confidence):
        raw = np.fromfile(str(source), dtype=np.uint8)
        frame = cv2.imdecode(raw, cv2.IMREAD_COLOR)
        if frame is None:
            raise DetectionError("图片无法读取，请使用有效的 JPG、PNG 或 WebP 文件。")
        started = time.perf_counter()
        with self._lock:
            result = self._get_model().predict(source=frame, conf=confidence, classes=self._class_ids, verbose=False)[0]
        encoded, buffer = cv2.imencode(".jpg", result.plot())
        if not encoded:
            raise DetectionError("检测结果图片保存失败。")
        buffer.tofile(str(destination))
        return self._objects(result), int((time.perf_counter() - started) * 1000)

    def video(self, source, destination, confidence):
        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise DetectionError("视频无法读取，请使用有效的 MP4、AVI 或 MOV 文件。")
        encoder = None
        started = time.perf_counter()
        objects = []
        try:
            fps = capture.get(cv2.CAP_PROP_FPS)
            if not 1 <= fps <= 120:
                fps = 25
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if width <= 0 or height <= 0:
                raise DetectionError("视频尺寸无效。")
            size = (width + width % 2, height + height % 2)
            encoder = subprocess.Popen(
                [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
                 "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "bgr24",
                 "-s", f"{size[0]}x{size[1]}", "-r", str(fps), "-i", "-",
                 "-an", "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                 "-movflags", "+faststart", str(destination)],
                stdin=subprocess.PIPE, stderr=subprocess.DEVNULL,
            )
            frame_index = 0
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if frame_index >= MAX_VIDEO_FRAMES:
                    raise DetectionError(f"视频超过 {MAX_VIDEO_FRAMES} 帧的处理上限。")
                with self._lock:
                    result = self._get_model().predict(source=frame, conf=confidence, classes=self._class_ids, verbose=False)[0]
                objects.extend(self._objects(result, frame_index))
                annotated = result.plot()
                if annotated.shape[1] != size[0] or annotated.shape[0] != size[1]:
                    annotated = cv2.copyMakeBorder(annotated, 0, size[1] - height, 0, size[0] - width,
                                                   cv2.BORDER_CONSTANT)
                try:
                    encoder.stdin.write(annotated.tobytes())
                except BrokenPipeError:
                    raise DetectionError("结果视频编码失败，请检查 FFmpeg 编码器。") from None
                frame_index += 1
            if frame_index == 0:
                raise DetectionError("视频中没有可读取的画面。")
        finally:
            capture.release()
            if encoder is not None:
                try:
                    encoder.stdin.close()
                except BrokenPipeError:
                    pass
                exit_code = encoder.wait()
        if exit_code != 0:
            raise DetectionError("结果视频编码失败，请检查 FFmpeg 编码器。")
        return objects, int((time.perf_counter() - started) * 1000), frame_index


yolo_service = YOLOService()
