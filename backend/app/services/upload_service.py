def save_media(file_storage, upload_dir):
    """Stub for saving uploaded files."""
    filename = file_storage.filename
    file_path = f"{upload_dir}/{filename}"
    file_storage.save(file_path)
    return file_path
