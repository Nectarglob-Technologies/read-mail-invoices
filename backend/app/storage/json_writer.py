import json
import os
from datetime import datetime
from backend.app.core.config import OUTPUT_DIR


def save_json(data: dict):
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filename = f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(OUTPUT_DIR, filename)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✅ JSON saved: {path}")

        return path

    except Exception as e:
        print("❌ JSON SAVE ERROR:", e)
        return None
