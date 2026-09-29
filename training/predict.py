"""Quick local check of trained weights before plugging them into the web app."""

import argparse
import os
from pathlib import Path

os.environ.setdefault("YOLO_CONFIG_DIR", str(Path(__file__).resolve().parents[1] / ".ultralytics"))

from ultralytics import YOLO  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Preview a YOLO model on one image or video")
    parser.add_argument("source", type=Path)
    parser.add_argument("--weights", type=Path, default=Path(__file__).resolve().parents[1] / "backend/models/best.pt")
    parser.add_argument("--conf", type=float, default=0.5)
    args = parser.parse_args()
    if not args.source.is_file() or not args.weights.is_file():
        parser.error("Source and weights files must exist")
    output = Path(__file__).resolve().parent / "runs" / "preview"
    model = YOLO(str(args.weights))
    # Exhaust the generator so video frames are actually processed.
    for _ in model.predict(source=str(args.source), conf=args.conf, save=True,
                           project=str(output.parent), name=output.name, exist_ok=True,
                           stream=True, verbose=False):
        pass
    print(f"Preview: {output}")


if __name__ == "__main__":
    main()
