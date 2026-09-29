"""Compare hard-hat checkpoints on the same locally prepared YOLO test split."""

import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / ".ultralytics"))
sys.path.insert(0, str(ROOT / "backend"))

from ultralytics import YOLO  # noqa: E402
from services.helmet_policy import helmet_class_ids, wearing_status  # noqa: E402


DEFAULT_MODELS = {
    "motorcycle_helmet": ROOT / "model_zoo/helmet/best.pt",
    "hardhat_keremberke": ROOT / "model_zoo/hardhat_keremberke/best.pt",
    "hardhat_construction": ROOT / "model_zoo/hardhat_construction/best.pt",
    "ppe": ROOT / "model_zoo/ppe/best.pt",
}


def overlap(a, b) -> float:
    left, top, right, bottom = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0, right - left) * max(0, bottom - top)
    area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    return intersection / (area_a + area_b - intersection) if area_a + area_b > intersection else 0.0


def labels_for(image: Path, dataset: Path) -> list[tuple[int, list[float]]]:
    label = dataset / "labels" / "test" / f"{image.stem}.txt"
    result = []
    for line in label.read_text(encoding="utf-8").splitlines():
        category, cx, cy, width, height = map(float, line.split())
        result.append((int(category), [cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2]))
    return result


def evaluate(name: str, weight: Path, images: list[Path], dataset: Path, confidence: float) -> dict:
    model = YOLO(str(weight))
    ids = helmet_class_ids(model.names)
    counts = {"Hardhat": {"tp": 0, "fp": 0, "fn": 0}, "NO-Hardhat": {"tp": 0, "fp": 0, "fn": 0}}
    for image, prediction in zip(images, model.predict(source=[str(path) for path in images],
                                                 classes=ids, conf=confidence, imgsz=640,
                                                 device="cpu", stream=True, verbose=False)):
        width, height = prediction.orig_shape[1], prediction.orig_shape[0]
        truths = labels_for(image, dataset)
        matched = set()
        boxes = sorted(prediction.boxes, key=lambda box: float(box.conf.item()), reverse=True)
        for box in boxes:
            status = wearing_status(model.names[int(box.cls.item())])
            category = 0 if status == "compliant" else 1
            label = "Hardhat" if category == 0 else "NO-Hardhat"
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            predicted = [x1 / width, y1 / height, x2 / width, y2 / height]
            candidates = [(overlap(predicted, true_box), index) for index, (true_class, true_box) in enumerate(truths)
                          if true_class == category and index not in matched]
            best_iou, best_index = max(candidates, default=(0.0, -1))
            if best_iou >= 0.5:
                counts[label]["tp"] += 1
                matched.add(best_index)
            else:
                counts[label]["fp"] += 1
        for index, (category, _) in enumerate(truths):
            if index not in matched:
                counts["Hardhat" if category == 0 else "NO-Hardhat"]["fn"] += 1
    for item in counts.values():
        item["precision"] = round(item["tp"] / (item["tp"] + item["fp"]), 4) if item["tp"] + item["fp"] else 0.0
        item["recall"] = round(item["tp"] / (item["tp"] + item["fn"]), 4) if item["tp"] + item["fn"] else 0.0
    print(f'{name}: {counts}', flush=True)
    return {"model": name, "classes": model.names, "counts": counts}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "training/dataset/hardhat")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--only", choices=DEFAULT_MODELS, help="Evaluate one model")
    args = parser.parse_args()
    images = sorted((args.dataset / "images" / "test").glob("*.jpg"))
    if not images:
        parser.error("No test images; run training/prepare_hardhat_data.py --test 48 first")
    selected = {args.only: DEFAULT_MODELS[args.only]} if args.only else DEFAULT_MODELS
    report = {
        "dataset": "keremberke/hard-hat-detection test split, first N rows",
        "images": len(images),
        "confidence": args.conf,
        "iou": 0.5,
        "metric_note": "Box-level precision and recall at fixed confidence; not mAP or worker-level compliance",
        "results": [evaluate(name, weight, images, args.dataset, args.conf) for name, weight in selected.items()],
    }
    output = ROOT / "training/evaluations/hardhat_comparison.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
