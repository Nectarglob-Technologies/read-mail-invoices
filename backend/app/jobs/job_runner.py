import json
import os
from datetime import datetime
from uuid import uuid4

from backend.app.core.config import DATA_DIR

JOBS_DIR = os.path.join(DATA_DIR, "jobs")
os.makedirs(JOBS_DIR, exist_ok=True)


def create_job(filename: str):
    job_id = str(uuid4())

    job_data = {
        "job_id": job_id,
        "filename": filename,
        "status": "PROCESSING",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": None,
        "result": None,
        "error": None
    }

    path = os.path.join(JOBS_DIR, f"{job_id}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(job_data, f, indent=2)

    return job_id, path


def update_job(job_id: str, status: str, result=None, error=None):
    path = os.path.join(JOBS_DIR, f"{job_id}.json")

    if not os.path.exists(path):
        print(f"❌ Job not found: {job_id}")
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["status"] = status
    data["updated_at"] = datetime.utcnow().isoformat()

    if result is not None:
        data["result"] = result

    if error is not None:
        data["error"] = str(error)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return data


def get_job(job_id: str):
    path = os.path.join(JOBS_DIR, f"{job_id}.json")

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
