"""Image tools: compression and background removal."""
import io
import os

import httpx
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from fastapi.concurrency import run_in_threadpool

router = APIRouter(prefix="/api/image", tags=["image-tools"])

ALLOWED = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 20 * 1024 * 1024
REMOVE_BG_URL = "https://api.remove.bg/v1.0/removebg"

# Cached offline model session (created lazily on first fallback use)
_rembg_session = None


async def _read_image(file: UploadFile) -> bytes:
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image exceeds the 20 MB upload limit.")
    if not data:
        raise HTTPException(400, "Empty file.")
    from PIL import Image
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
    except Exception:
        raise HTTPException(415, "Invalid or corrupt image.")
    return data


@router.post("/compress")
async def compress_image(file: UploadFile = File(...), quality: int = Form(75), max_width: int = Form(0)):
    from PIL import Image
    data = await _read_image(file)
    quality = max(5, min(95, quality))
    im = Image.open(io.BytesIO(data))
    fmt = (im.format or "JPEG").upper()
    if max_width and im.width > max_width:
        im = im.resize((max_width, int(im.height * max_width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    if fmt == "PNG":
        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        if has_alpha:
            im.convert("RGBA").quantize(colors=max(16, int(256 * quality / 95)), method=Image.FASTOCTREE).save(buf, "PNG", optimize=True)
            media, ext = "image/png", "png"
        else:
            im.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True)
            media, ext = "image/jpeg", "jpg"
    elif fmt == "WEBP":
        im.save(buf, "WEBP", quality=quality)
        media, ext = "image/webp", "webp"
    else:
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(buf, "JPEG", quality=quality, optimize=True)
        media, ext = "image/jpeg", "jpg"
    out = buf.getvalue()
    if len(out) >= len(data):
        out, media = data, file.content_type or "application/octet-stream"
        ext = (file.filename or "img.jpg").rsplit(".", 1)[-1]
    stem = (file.filename or "image").rsplit(".", 1)[0]
    return Response(content=out, media_type=media, headers={
        "Content-Disposition": f'attachment; filename="{stem}_compressed.{ext}"',
    })


@router.post("/remove-bg")
async def remove_background(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED:
        raise HTTPException(415, "Upload a JPEG, PNG or WebP image.")
    data = await _read_image(file)

    # 1) Try each remove.bg key in turn. When a key runs out of quota / is
    #    rejected / rate-limited, automatically move on to the next key.
    png = await _removebg_via_api(data, file.filename, file.content_type)
    engine = "remove.bg"

    # 2) If every key is exhausted or unavailable, fall back to a free
    #    fully-offline engine so the tool keeps working no matter what.
    if png is None:
        try:
            png = await run_in_threadpool(_rembg_remove, data)
            engine = "offline"
        except Exception:
            raise HTTPException(502, "Background removal is temporarily unavailable. Please try again in a moment.")

    stem = (file.filename or "image").rsplit(".", 1)[0]
    return Response(content=png, media_type="image/png", headers={
        "Content-Disposition": f'attachment; filename="{stem}_no_bg.png"',
        "X-Bg-Engine": engine,
        "Access-Control-Expose-Headers": "X-Bg-Engine, Content-Disposition",
    })


def _removebg_keys():
    """Collect all configured remove.bg keys (supports a comma-separated list)."""
    keys = []
    for src in (os.environ.get("REMOVEBG_API_KEYS", ""), os.environ.get("REMOVEBG_API_KEY", "")):
        for k in src.split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)
    return keys


async def _removebg_via_api(data: bytes, filename: str, content_type: str):
    """Try remove.bg with each key. Returns transparent PNG bytes, or None if
    no key could complete the job (so the caller can use the offline fallback)."""
    keys = _removebg_keys()
    for key in keys:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
                resp = await client.post(
                    REMOVE_BG_URL,
                    headers={"X-Api-Key": key},
                    files={"image_file": (filename or "upload", data, content_type or "application/octet-stream")},
                    data={"size": "auto", "format": "png"},
                )
        except (httpx.TimeoutException, httpx.RequestError):
            # network hiccup for this key -> try the next one
            continue
        if resp.status_code == 200:
            return resp.content
        # 401 invalid, 402 out of credits, 403 forbidden, 429 rate-limited, or
        # any other error -> quietly rotate to the next key.
        continue
    return None


def _rembg_remove(data: bytes) -> bytes:
    """Free offline background removal (used only when all API keys fail)."""
    global _rembg_session
    from rembg import remove, new_session
    if _rembg_session is None:
        _rembg_session = new_session("u2net")
    return remove(data, session=_rembg_session)
