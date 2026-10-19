import json

def make_alert(event, detector):
    return {"event_id": event["event_id"], "ts": event["ts"], "key_id": event["key_id"],
            "nonce_prefix": event["nonce"][:8] + "...", "detector": detector, "severity": "HIGH",
            "reason": "Nonce đã xuất hiện trước đó với cùng khóa (nguy cơ lộ keystream)"}

def write_alerts(path, events, preds, detector, limit=200):
    with open(path, "w", encoding="utf-8") as f:
        count = 0
        for e, p in zip(events, preds):
            if p and count < limit:
                f.write(json.dumps(make_alert(e, detector), ensure_ascii=False) + "\n")
                count += 1