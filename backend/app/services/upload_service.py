import os
import uuid
from werkzeug.utils import secure_filename


def save_media(file_storage, upload_dir):
    """Save uploaded file and return filename."""
    os.makedirs(upload_dir, exist_ok=True)
    original = secure_filename(file_storage.filename or "")
    _, ext = os.path.splitext(original)
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, filename)
    file_storage.save(file_path)
    return filename
