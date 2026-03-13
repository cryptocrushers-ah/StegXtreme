import mimetypes
from core.backends.image import ImageBackend
from core.backends.audio import AudioBackend
from core.backends.video import VideoBackend

mimetypes.init()

def get_backend(filepath: str):
    """
    Returns the appropriate backend class based on the file's MIME type.
    """
    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type:
        # Fallback by extension
        ext = filepath.lower().split('.')[-1]
        if ext in ['png', 'jpg', 'jpeg', 'bmp']:
            return ImageBackend
        elif ext in ['wav', 'mp3', 'flac']:
            return AudioBackend
        elif ext in ['mp4', 'avi', 'mkv']:
            return VideoBackend
        raise ValueError(f"Unknown file type for {filepath}")

    if mime_type.startswith('image/'):
        return ImageBackend
    elif mime_type.startswith('audio/'):
        return AudioBackend
    elif mime_type.startswith('video/'):
        return VideoBackend
    else:
        raise ValueError(f"Unsupported MIME type: {mime_type}")
