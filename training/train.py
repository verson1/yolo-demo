"""Train a custom detection model and optionally install its best.pt into the app."""

import argparse
import json
import os
import shutil
from pathlib import Path

import yaml


HERE = Path(__file__).resolve().parent
os.environ.setdefault("YOLO_CONFIG_DIR", str(HERE.parent / ".ultralytics"))
os.environ.setdefault("MPLCONFIGDIR", str(HERE.parent / ".matplotlib"))

from ultralytics import YOLO  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Train a YOLO detection model")
    parser.add_argument("--data", type=Path, default=HERE / "data.yaml")
    parser.add_argument("--model", default="yolo11n.pt", help="Pretrained weight path or model name")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--fraction", type=float, default=1.0, help="Fraction of training images; use 0.1 for a quick pipeline check")
    parser.add_argument("--workers", type=int, default=0, help="Data loader workers; 0 is stable on Windows")
    parser.add_argument("--device", default=None, help="e.g. 0, cpu; default: Ultralytics auto")
    parser.add_argument("--name", default="custom")
    parser.add_argument("--install", action="store_true", help="Copy best.pt into backend/models/")
    args = parser.parse_args()
    data_file = args.data.resolve()
    if not data_file.is_file():
        parser.error(f"Dataset config not found: {data_file}")
    if args.epochs < 1 or args.imgsz < 32 or args.batch < 1 or not 0 < args.fraction <= 1 or args.workers < 0:
        parser.error("epochs, imgsz, batch, fraction and workers are invalid")

    config = yaml.safe_load(data_file.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not {"train", "val", "names"} <= config.keys():
        parser.error("data.yaml needs train, val and names")
    dataset_root = Path(config.get("path", "."))
    if not dataset_root.is_absolute():
        dataset_root = (data_file.parent / dataset_root).resolve()
    if not dataset_root.is_dir():
        parser.error(f"Dataset folder not found: {dataset_root}")
    config["path"] = str(dataset_root)
    project = HERE / "runs"
    project.mkdir(exist_ok=True)
    resolved_data = project / f"{args.name}-data.yaml"
    resolved_data.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8")

    # Ultralytics checks for Arial while reading a dataset, even with plots disabled.
    # Use the system copy on Windows so an offline training run does not download it.
    font_target = Path(os.environ["YOLO_CONFIG_DIR"]) / "Ultralytics" / "Arial.ttf"
    system_font = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "arial.ttf"
    if not font_target.is_file() and system_font.is_file():
        font_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(system_font, font_target)

    model = YOLO(args.model)
    if model.task != "detect":
        parser.error("This template requires an object-detection model")
    model.train(data=str(resolved_data), epochs=args.epochs, imgsz=args.imgsz,
                batch=args.batch, fraction=args.fraction, workers=args.workers,
                device=args.device, project=str(project), name=args.name,
                exist_ok=True)
    best = project / args.name / "weights" / "best.pt"
    if not best.is_file():
        raise FileNotFoundError(f"Training finished without best.pt: {best}")
    print(f"Best weights: {best}")
    if args.install:
        target = HERE.parent / "backend" / "models" / "best.pt"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best, target)
        (target.parent / "active.json").write_text(
            json.dumps({"id": f"custom-{args.name}", "name": args.name}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Installed: {target} (restart Flask to load the new model)")


if __name__ == "__main__":
    main()
