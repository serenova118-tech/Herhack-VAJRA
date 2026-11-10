"""Build a metadata-free copy of an image, entirely in memory."""
from io import BytesIO

from PIL import Image, ImageOps

from .uploads import UploadError, check_image_size

_FORBIDDEN_INFO = {"exif", "icc_profile", "xmp", "photoshop", "comment", "Comment"}


def clean_image_bytes(data: bytes) -> tuple[bytes, str]:
    """Return (cleaned_bytes, format) for a PNG or JPEG.

    Pixels are re-encoded into a fresh image; EXIF, XMP, ICC profile, comments
    and text chunks are not carried over. EXIF orientation is applied to the
    pixels first so the picture does not appear rotated once EXIF is gone.
    The result is re-opened and checked before it is returned.
    """
    with Image.open(BytesIO(data)) as src:
        fmt = src.format
        if fmt not in ("PNG", "JPEG"):
            raise UploadError("Metadata cleaning supports PNG and JPEG images only.", 400)
        check_image_size(src.width, src.height)
        src.load()
        oriented = ImageOps.exif_transpose(src)
        clean = oriented.copy()
        # Keep only what is needed to render palette transparency correctly.
        clean.info = {k: v for k, v in oriented.info.items() if k == "transparency"}

    if fmt == "JPEG":
        if clean.mode not in ("RGB", "L", "CMYK"):
            clean = clean.convert("RGB")
        kwargs = {"quality": 95}
    else:
        kwargs = {}
    out = BytesIO()
    clean.save(out, format=fmt, **kwargs)
    result = out.getvalue()
    _verify_clean(result)
    return result, fmt


def _verify_clean(data: bytes) -> None:
    with Image.open(BytesIO(data)) as img:
        leftovers = [k for k in img.info if k in _FORBIDDEN_INFO or str(k).startswith("XML:")]
        text = getattr(img, "text", None)
        if len(img.getexif()) or leftovers or text:
            raise RuntimeError("Cleaned image still contains metadata.")