"""Select a downloaded checkpoint as the web app's active detection model."""

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CATALOG = {item["id"]: item for item in json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id", choices=CATALOG)
    args = parser.parse_args()
    item = CATALOG[args.id]
    source = ROOT / item["id"] / item["filename"]
    if not source.is_file():
        parser.error(f"Download first: python model_zoo/download_models.py {args.id}")
    with source.open("rb") as file:
        digest = hashlib.file_digest(file, "sha256").hexdigest()
    if digest != item["sha256"]:
        parser.error(f"SHA-256 mismatch for {source}")
    destination = ROOT.parent / "backend" / "models"
    destination.mkdir(parents=True, exist_ok=True)
    staged = destination / "best.pt.new"
    with source.open("rb") as input_file, staged.open("wb") as output_file:
        shutil.copyfileobj(input_file, output_file)
    os.replace(staged, destination / "best.pt")
    metadata = destination / "active.json"
    staged_metadata = destination / "active.json.new"
    staged_metadata.write_text(json.dumps({"id": args.id, "name": item["direction"], "source": item["source"], "sha256": digest}, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(staged_metadata, metadata)
    print(f'Active model: {item["direction"]} ({args.id}). Restart Flask to load it.')


if __name__ == "__main__":
    main()
