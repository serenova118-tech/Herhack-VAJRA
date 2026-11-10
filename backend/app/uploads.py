"""Upload safety helpers: bounded reading and content-vs-extension validation."""
import io
import zipfile

# Images are decoded in memory; refuse absurd dimensions (decompression bombs).
MAX_IMAGE_PIXELS = 50_000_000
MAX_DOCX_UNCOMPRESSED = 100 * 1024 * 1024
MAX_DOCX_ENTRIES = 5000


class UploadError(Exception):
    """Error whose message is safe to show to the end user."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def read_limited(file, max_bytes: int, chunk_size: int = 1024 * 1024) -> bytes:
    """Read an upload in chunks and stop as soon as the limit is exceeded."""
    chunks, total = [], 0
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise UploadError(
                f"File is larger than the {max_bytes // (1024 * 1024)} MB limit.", 413)
        chunks.append(chunk)
    if total == 0:
        raise UploadError("File is empty.", 400)
    return b"".join(chunks)


_MISMATCH = "The file content does not match its extension."


def validate_content(data: bytes, suffix: str) -> None:
    """Check magic bytes / container structure against the claimed extension."""
    if suffix == ".png":
        ok = data.startswith(b"\x89PNG\r\n\x1a\n")
    elif suffix in (".jpg", ".jpeg"):
        ok = data.startswith(b"\xff\xd8\xff")
    elif suffix == ".pdf":
        ok = b"%PDF-" in data[:1024]
    elif suffix == ".docx":
        ok = _looks_like_docx(data)
    else:
        raise UploadError("Unsupported file type.", 400)
    if not ok:
        raise UploadError(_MISMATCH, 400)


def _looks_like_docx(data: bytes) -> bool:
    if not data.startswith(b"PK"):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            infos = zf.infolist()
            if len(infos) > MAX_DOCX_ENTRIES:
                raise UploadError("The document contains too many internal parts.", 400)
            if sum(i.file_size for i in infos) > MAX_DOCX_UNCOMPRESSED:
                raise UploadError("The document expands to an unsafe size.", 400)
            names = {i.filename for i in infos}
            return "[Content_Types].xml" in names and "word/document.xml" in names
    except zipfile.BadZipFile:
        return False


def check_image_size(width: int, height: int) -> None:
    if width * height > MAX_IMAGE_PIXELS:
        raise UploadError("Image dimensions are too large to process safely.", 413)
