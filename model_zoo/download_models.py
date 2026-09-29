"""Download pinned public detection checkpoints and verify their SHA-256 hashes."""

import argparse
import hashlib
import json
import urllib.request
from urllib.parse import quote
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CATALOG = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))


def download_sample(item: dict) -> None:
    sample = item.get("sample")
    if not sample:
        return
    target = ROOT / item["id"] / "sample.jpg"
    if target.exists():
        return
    url = f'https://huggingface.co/{item["repo"]}/resolve/{item["revision"]}/{quote(sample)}?download=true'
    request = urllib.request.Request(url, headers={"User-Agent": "yolo-template-model-zoo/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    print(f'SAMPLE {item["id"]}: {target.stat().st_size} bytes', flush=True)


def download(item: dict) -> None:
    target = ROOT / item["id"] / item["filename"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if item.get("repo"):
        url = f'https://huggingface.co/{item["repo"]}/resolve/{item["revision"]}/{item["filename"]}?download=true'
    else:
        url = item["url"]
    if target.exists():
        digest = hashlib.file_digest(target.open("rb"), "sha256").hexdigest()
        if not item["sha256"] or digest == item["sha256"]:
            print(f'SKIP {item["id"]}: {target} sha256={digest}', flush=True)
            return
    partial = target.with_name(target.name + ".part")
    print(f'GET  {item["id"]}: {url}', flush=True)
    request = urllib.request.Request(url, headers={"User-Agent": "yolo-template-model-zoo/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response, partial.open("wb") as output:
        digest = hashlib.sha256()
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
            digest.update(chunk)
    actual = digest.hexdigest()
    if item["sha256"] and actual != item["sha256"]:
        partial.unlink()
        raise ValueError(f'{item["id"]}: SHA-256 mismatch: {actual}')
    partial.replace(target)
    print(f'OK   {item["id"]}: {target.stat().st_size} bytes sha256={actual}', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", help="Catalog IDs; default: all")
    parser.add_argument("--samples", action="store_true", help="Also fetch available model-card sample images")
    args = parser.parse_args()
    selected = [item for item in CATALOG if not args.ids or item["id"] in args.ids]
    missing = set(args.ids) - {item["id"] for item in selected}
    if missing:
        parser.error(f"Unknown IDs: {', '.join(sorted(missing))}")
    for item in selected:
        download(item)
        if args.samples:
            download_sample(item)
    if args.samples:
        target = ROOT / "bus.jpg"
        if not target.exists():
            request = urllib.request.Request("https://ultralytics.com/images/bus.jpg", headers={"User-Agent": "yolo-template-model-zoo/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            print(f'SAMPLE general: {target.stat().st_size} bytes', flush=True)


if __name__ == "__main__":
    main()
