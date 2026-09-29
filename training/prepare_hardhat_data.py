"""Fetch a reproducible subset of the public construction hard-hat dataset."""

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parent
DESTINATION = ROOT / "dataset" / "hardhat"
DATASET = "keremberke/hard-hat-detection"
BASE_URL = "https://datasets-server.huggingface.co/rows"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "yolo-hardhat-template/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return response.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def download_split(remote: str, local: str, limit: int) -> None:
    if limit <= 0:
        return
    images = DESTINATION / "images" / local
    labels = DESTINATION / "labels" / local
    images.mkdir(parents=True, exist_ok=True)
    labels.mkdir(parents=True, exist_ok=True)
    for offset in range(0, limit, 100):
        query = urllib.parse.urlencode({"dataset": DATASET, "config": "full", "split": remote,
                                        "offset": offset, "length": min(100, limit - offset)})
        page = json.loads(fetch(f"{BASE_URL}?{query}"))
        for entry in page["rows"]:
            index = entry["row_idx"]
            row = entry["row"]
            image = images / f"{index:06}.jpg"
            label = labels / f"{index:06}.txt"
            if image.is_file() and label.is_file():
                continue
            raw = fetch(row["image"]["src"])
            frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError(f"Unreadable image in {remote} row {index}")
            height, width = frame.shape[:2]
            lines = []
            for category, (x, y, box_width, box_height) in zip(row["objects"]["category"], row["objects"]["bbox"]):
                if category not in (0, 1) or box_width <= 0 or box_height <= 0:
                    continue
                cx = (x + box_width / 2) / width
                cy = (y + box_height / 2) / height
                lines.append(f"{category} {cx:.6f} {cy:.6f} {box_width / width:.6f} {box_height / height:.6f}")
            if not cv2.imwrite(str(image), frame):
                raise OSError(f"Could not save {image}")
            label.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        print(f"{local}: {min(offset + 100, limit)}/{limit}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=int, default=0, help="0-13782")
    parser.add_argument("--val", type=int, default=0, help="0-3962")
    parser.add_argument("--test", type=int, default=0, help="0-2001")
    args = parser.parse_args()
    for value, maximum, name in ((args.train, 13782, "train"), (args.val, 3962, "val"), (args.test, 2001, "test")):
        if value < 0 or value > maximum:
            parser.error(f"{name} must be within 0..{maximum}")
    for remote, local, limit in (("train", "train", args.train), ("validation", "val", args.val), ("test", "test", args.test)):
        download_split(remote, local, limit)
    print(f"Dataset ready: {DESTINATION}")


if __name__ == "__main__":
    main()
