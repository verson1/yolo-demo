"""Exercise image upload, MySQL persistence, media, summary and deletion."""

import argparse
from pathlib import Path
from uuid import uuid4

import cv2

from app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"Image missing: {args.image}")
    client = create_app().test_client()
    model = client.get("/api/model/info").get_json()
    assert model["ready"] and len(model["helmet_class_ids"]) >= 2, model
    record_ids = []
    video_path = Path(__file__).resolve().parent / "results" / f"smoke_{uuid4().hex}.avi"
    try:
        with args.image.open("rb") as image:
            response = client.post("/api/detect/image", data={"file": (image, args.image.name), "confidence": "0.25"})
        assert response.status_code == 201, response.get_json()
        created = response.get_json()
        record_id = created["id"]
        record_ids.append(record_id)
        assert created["helmet_count"] + created["no_helmet_count"] == created["total_objects"]
        assert created["model_id"] == model["model_id"]
        assert client.get(f"/api/records/{record_id}").status_code == 200
        assert client.get(f"/api/records/{record_id}/media/result").status_code == 200
        summary = client.get("/api/dashboard/summary")
        assert summary.status_code == 200, summary.get_json()
        print(f'PASS model={created["model_id"]} record={record_id} helmet={created["helmet_count"]} no_helmet={created["no_helmet_count"]}')
        frame = cv2.imread(str(args.image))
        assert frame is not None
        height, width = frame.shape[:2]
        writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"MJPG"), 5, (width, height))
        assert writer.isOpened()
        for _ in range(4):
            writer.write(frame)
        writer.release()
        with video_path.open("rb") as video:
            response = client.post("/api/detect/video", data={"file": (video, "smoke.avi"), "confidence": "0.25"})
        assert response.status_code == 201, response.get_json()
        created = response.get_json()
        record_ids.append(created["id"])
        assert created["frames"] == 4
        assert created["violation_frames"] <= created["frames"]
        assert client.get(f'/api/records/{created["id"]}/media/result').status_code == 200
        print(f'PASS video frames={created["frames"]} violation_frames={created["violation_frames"]}')
    finally:
        video_path.unlink(missing_ok=True)
        for record_id in reversed(record_ids):
            deleted = client.delete(f"/api/records/{record_id}")
            assert deleted.status_code == 204, deleted.get_data(as_text=True)


if __name__ == "__main__":
    main()
