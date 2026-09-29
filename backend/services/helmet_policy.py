"""Safety-helmet class mapping and event counts shared by image/video flows."""


COMPLIANT = {"hardhat", "helmet", "withhelmet", "戴安全帽", "佩戴安全帽"}
VIOLATION = {"nohardhat", "nohelmet", "withouthelmet", "未戴安全帽", "未佩戴安全帽"}


def wearing_status(label: str) -> str | None:
    key = "".join(char for char in str(label).lower() if char.isalnum())
    if key in COMPLIANT:
        return "compliant"
    if key in VIOLATION:
        return "violation"
    return None


def helmet_class_ids(names: dict) -> list[int]:
    found = {"compliant": [], "violation": []}
    for class_id, label in names.items():
        status = wearing_status(label)
        if status:
            found[status].append(int(class_id))
    if not all(found.values()):
        raise ValueError("模型需要同时包含安全帽和未佩戴安全帽两个类别。")
    return found["compliant"] + found["violation"]


def summarize(objects: list[dict], is_video: bool = False) -> dict:
    compliant = sum(item.get("wearing_status") == "compliant" for item in objects)
    violation = sum(item.get("wearing_status") == "violation" for item in objects)
    frames = len({item["frame_index"] for item in objects if item.get("wearing_status") == "violation" and item.get("frame_index") is not None}) if is_video else 0
    return {
        "helmet_count": compliant,
        "no_helmet_count": violation,
        "violation_frames": frames,
        "status": "violation" if violation else "compliant" if compliant else "unknown",
    }
