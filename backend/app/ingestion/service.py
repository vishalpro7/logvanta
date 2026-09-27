from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

RAW_DIR = Path(__file__).resolve().parents[3] / "../../data/raw"
RAW_DIR = RAW_DIR.resolve()
RAW_DIR.mkdir(parents=True, exist_ok=True)


def ingest(source: str, raw_log: str) -> dict:
    event_id = str(uuid4())
    received_at = datetime.now(timezone.utc).isoformat()
    record = {
        "event_id": event_id,
        "source": source,
        "received_at": received_at,
        "raw_log": raw_log,
    }
    path = RAW_DIR / f"{event_id}.log"
    path.write_text(raw_log, encoding="utf-8")
    return record
