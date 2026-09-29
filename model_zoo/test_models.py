"""Local compatibility smoke test; this does not measure detection accuracy."""

import argparse
import json
import os
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT.parent / ".ultralytics"))
Path(os.environ["YOLO_CONFIG_DIR"]).mkdir(parents=True, exist_ok=True)

import cv2  # noqa: E402
import torch  # noqa: E402
from ultralytics import YOLO  # noqa: E402


CATALOG = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
ALLOWED_GLOBAL_PREFIXES = ("torch.", "ultralytics.", "numpy.", "collections.", "builtins.", "albumentations.", "random.Random")


def test_one(item: dict) -> dict:
    path = ROOT / item["id"] / item["filename"]
    sample = ROOT / item["id"] / "sample.jpg"
    if not sample.exists():
        sample = ROOT / "bus.jpg"
    sample_kind = "generic_bus_image" if sample.name == "bus.jpg" else "raw_domain_image" if item["id"] == "pcb" else "annotated_model_card_montage"
    result = {"id": item["id"], "weight": str(path.relative_to(ROOT)), "sample": str(sample.relative_to(ROOT)), "sample_kind": sample_kind}
    try:
        if not path.is_file():
            raise FileNotFoundError(path)
        if cv2.imread(str(sample)) is None:
            raise ValueError(f"Unreadable test image: {sample}")
        unsafe = torch.serialization.get_unsafe_globals_in_checkpoint(path)
        unexpected = [name for name in unsafe if not name.startswith(ALLOWED_GLOBAL_PREFIXES)]
        result["checkpoint_globals"] = len(unsafe)
        if unexpected:
            raise ValueError(f"Unexpected checkpoint globals: {unexpected}")
        start = time.perf_counter()
        model = YOLO(str(path))
        result["task"] = model.task
        result["classes"] = model.names
        if model.task != "detect":
            raise ValueError(f"Not a detection checkpoint: {model.task}")
        prediction = model.predict(source=str(sample), device="cpu", imgsz=640, conf=0.25, verbose=False)[0]
        result["elapsed_seconds"] = round(time.perf_counter() - start, 3)
        result["detections"] = len(prediction.boxes)
        result["detected_classes"] = dict(Counter(model.names[int(index)] for index in prediction.boxes.cls.tolist()))
        if sample.name == "sample.jpg":
            out = ROOT / item["id"] / "test_output.jpg"
            if not cv2.imwrite(str(out), prediction.plot()):
                raise OSError(f"Could not save annotated image: {out}")
            result["output"] = str(out.relative_to(ROOT))
        result["status"] = "pass"
    except Exception as exc:
        result["status"] = "fail"
        result["error"] = f"{type(exc).__name__}: {exc}"
    print(f'{result["id"]:16} {result["status"]:4} classes={len(result.get("classes", {})):3} detections={result.get("detections", "-")} {result.get("error", "")}', flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", help="Catalog IDs; default: all")
    args = parser.parse_args()
    selected = [item for item in CATALOG if not args.ids or item["id"] in args.ids]
    missing = set(args.ids) - {item["id"] for item in selected}
    if missing:
        parser.error(f"Unknown IDs: {', '.join(sorted(missing))}")
    report = {
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"torch": torch.__version__, "ultralytics": __import__("ultralytics").__version__, "device": "cpu"},
        "purpose": "Load, task/class, and one-image inference compatibility only; no accuracy or safety evaluation",
        "results": [test_one(item) for item in selected],
    }
    (ROOT / "test_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if any(item["status"] != "pass" for item in report["results"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
