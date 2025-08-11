import re
from pathlib import Path
from typing import Optional
import uuid

UPLOADS_DIR = Path("/workspace/data/uploads")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or uuid.uuid4().hex[:12]


def save_uploaded_file(file_bytes: bytes, filename: str) -> str:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    target = UPLOADS_DIR / unique_name
    with open(target, "wb") as f:
        f.write(file_bytes)
    return str(target)