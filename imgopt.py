#!/usr/bin/env python3
"""Shared image optimisation used by download_assets.py (for newly downloaded
attachments) and optimize_assets.py (for a one-off pass over existing assets).

Airtable serves full-resolution originals — a shopfront photo can be 3264x2448
and 11 MB. That is far more than a mobile-first site needs, so shrink the long
edge and re-encode. Photos become JPEG (much smaller than PNG); images that
actually use transparency stay PNG.
"""
import pathlib
from PIL import Image

# Long edge in pixels. The site shows these as cards plus a full-screen
# lightbox, so 1600px is already more than any phone or laptop can display.
MAX_EDGE = 1600
JPEG_QUALITY = 82

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
JPEG_EXTS = {".jpg", ".jpeg"}


def _uses_alpha(im):
    """True only if the image has an alpha channel *and* some pixel is not opaque."""
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        alpha = im.convert("RGBA").getchannel("A")
        return alpha.getextrema()[0] < 255
    return False


def optimize_image(path, max_edge=MAX_EDGE, quality=JPEG_QUALITY):
    """Shrink/re-encode one image in place.

    Returns (final_path, bytes_before, bytes_after), or None if the file is not
    an image we handle. The result is only kept when it is actually smaller,
    so running this repeatedly is safe and idempotent.

    The extension is preserved for files that are already JPEG (some are
    referenced by hard-coded paths, e.g. the club logo and the maintenance
    photo). Only PNG-without-transparency is converted to .jpg, and those are
    all discovered by glob in build_data.py, so the rename is safe.
    """
    path = pathlib.Path(path)
    suffix = path.suffix.lower()
    if suffix not in IMAGE_EXTS or not path.exists():
        return None

    before = path.stat().st_size
    try:
        with Image.open(path) as im:
            im.load()
            width, height = im.size
            scale = max_edge / max(width, height)
            if scale < 1.0:
                im = im.resize((max(1, round(width * scale)),
                                max(1, round(height * scale))),
                               Image.Resampling.LANCZOS)

            if _uses_alpha(im):
                target = path.with_suffix(".png")
                save_kwargs = dict(format="PNG", optimize=True)
                out = im if im.mode in ("RGBA", "LA", "P") else im.convert("RGBA")
            else:
                # keep .jpeg/.JPG as-is, otherwise settle on .jpg
                target = path if suffix in JPEG_EXTS else path.with_suffix(".jpg")
                save_kwargs = dict(format="JPEG", quality=quality,
                                   optimize=True, progressive=True)
                out = im.convert("RGB")

            tmp = path.with_name(path.name + ".opt.tmp")
            out.save(tmp, **save_kwargs)
    except Exception as exc:  # corrupt/unsupported file: leave it untouched
        print(f"  ! skipped {path.name}: {exc}")
        return None

    after = tmp.stat().st_size
    if after >= before and target == path:
        # no gain and no rename needed - keep the original bytes
        tmp.unlink()
        return (path, before, before)

    tmp.replace(target)
    if target != path:
        path.unlink(missing_ok=True)
    return (target, before, after)


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
