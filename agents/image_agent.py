"""
Image Generation Agent — Multi-provider AI image generation.
Supports: OpenRouter (FLUX, GPT Image, Gemini), Krea.ai, Pollinations.ai (free).
"""
import os
import uuid
import logging
import requests
import urllib.parse
import json
import time
import base64
import re

from config import Config

logger = logging.getLogger(__name__)

# ── Style & Size Maps ─────────────────────────────
IMAGE_STYLES = {
    "digital-art": "vibrant digital art, stylized, modern CG illustration",
    "realistic": "photorealistic, high detail, professional photography",
    "abstract": "abstract geometric art, bold shapes, creative composition",
    "neon-tech": "neon glow, cyberpunk aesthetic, dark background, tech futuristic",
    "minimalist": "clean minimalist design, simple shapes, white space",
    "auto": "modern digital illustration, professional quality",
}

IMAGE_SIZES = {
    "landscape": (1024, 576),
    "square": (1024, 1024),
    "portrait": (576, 1024),
    "auto": (1024, 576),
}

# ── Available Image Models ──────────────────────────
IMAGE_MODELS = {
    "openrouter": {
        "flux-2-pro": {
            "id": "black-forest-labs/flux-2-pro",
            "name": "FLUX.2 Pro",
            "provider": "OpenRouter",
        },
        "gpt-image": {
            "id": "openai/gpt-image-1",
            "name": "GPT Image (OpenAI)",
            "provider": "OpenRouter",
        },
        "gemini-image": {
            "id": "google/gemini-2.5-flash-preview-image-generation",
            "name": "Gemini Flash Image",
            "provider": "OpenRouter",
        },
        "seedream": {
            "id": "bytedance/seedream-4.5",
            "name": "Seedream 4.5",
            "provider": "OpenRouter",
        },
    },
    "krea": {
        "flux-dev": {
            "id": "bfl/flux-1-dev",
            "name": "FLUX Dev",
            "provider": "Krea.ai",
        },
    },
    "free": {
        "pollinations": {
            "id": "pollinations",
            "name": "Pollinations (Free)",
            "provider": "Free",
        },
        "picsum": {
            "id": "picsum",
            "name": "Picsum Random (Fallback)",
            "provider": "Free",
        },
    },
}


def get_available_models() -> list[dict]:
    """Return list of available image models."""
    models = []
    if Config.OPENROUTER_API_KEY:
        for key, m in IMAGE_MODELS["openrouter"].items():
            models.append({**m, "key": f"openrouter/{key}", "available": True})
    krea_key = os.getenv("KREA_API_KEY", "")
    if krea_key:
        for key, m in IMAGE_MODELS["krea"].items():
            models.append({**m, "key": f"krea/{key}", "available": True})
    for key, m in IMAGE_MODELS["free"].items():
        models.append({**m, "key": f"free/{key}", "available": True})
    return models


def _build_prompt(title: str, summary: str, style: str = "auto") -> str:
    """Build a smart image prompt based on content and chosen style."""
    style_desc = IMAGE_STYLES.get(style, IMAGE_STYLES["auto"])
    # Truncate for URL safety and quality
    clean_title = title[:80].strip()
    clean_summary = summary[:100].strip() if summary else ""
    prompt = f"{style_desc}: {clean_title}"
    if clean_summary:
        prompt += f". {clean_summary}"
    prompt += ". No text, no watermarks, high quality"
    return prompt


def _gen_openrouter(prompt: str, model_key: str, filepath: str) -> dict:
    """Generate image via OpenRouter using modality parameter."""
    model_info = IMAGE_MODELS["openrouter"].get(model_key)
    if not model_info:
        return {"success": False, "error": f"Unknown model: {model_key}"}

    api_key = Config.OPENROUTER_API_KEY
    if not api_key:
        return {"success": False, "error": "OpenRouter API key not configured"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-trends-platform.local",
    }

    payload = {
        "model": model_info["id"],
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image"],
    }

    try:
        logger.info("Generating image via OpenRouter %s", model_info["id"])
        resp = requests.post(
            f"{Config.OPENROUTER_BASE_URL}/chat/completions",
            headers=headers, json=payload, timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return {"success": False, "error": "No choices in response"}

        msg = choices[0].get("message", {})
        content = msg.get("content", "")

        # Try multipart content
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    img_url = part.get("image_url", {}).get("url", "")
                    if img_url.startswith("data:"):
                        b64 = img_url.split(",", 1)[1] if "," in img_url else img_url
                        with open(filepath, "wb") as f:
                            f.write(base64.b64decode(b64))
                        return {"success": True, "filepath": filepath, "method": "openrouter"}
                    elif img_url:
                        img_resp = requests.get(img_url, timeout=30)
                        with open(filepath, "wb") as f:
                            f.write(img_resp.content)
                        return {"success": True, "filepath": filepath, "method": "openrouter"}

        # Try text content for base64 or URLs
        if isinstance(content, str):
            b64_match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', content)
            if b64_match:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(b64_match.group(1)))
                return {"success": True, "filepath": filepath, "method": "openrouter"}
            url_match = re.search(r'https?://\S+\.(?:png|jpg|jpeg|webp)', content)
            if url_match:
                img_resp = requests.get(url_match.group(0), timeout=30)
                with open(filepath, "wb") as f:
                    f.write(img_resp.content)
                return {"success": True, "filepath": filepath, "method": "openrouter"}

        return {"success": False, "error": "No image found in OpenRouter response"}
    except Exception as e:
        logger.warning("OpenRouter image gen failed: %s", e)
        return {"success": False, "error": str(e)}


def _gen_krea(prompt: str, model_key: str, filepath: str,
              width: int = 1024, height: int = 576) -> dict:
    """Generate image via Krea.ai async job API."""
    model_info = IMAGE_MODELS["krea"].get(model_key)
    if not model_info:
        return {"success": False, "error": f"Unknown Krea model: {model_key}"}
    krea_key = os.getenv("KREA_API_KEY", "")
    if not krea_key:
        return {"success": False, "error": "Krea.ai API key not configured"}

    headers = {
        "Authorization": f"Bearer {krea_key}",
        "Content-Type": "application/json",
    }
    try:
        logger.info("Generating image via Krea.ai %s", model_info["id"])
        resp = requests.post(
            f"https://api.krea.ai/generate/image/{model_info['id']}",
            headers=headers,
            json={"prompt": prompt, "width": width, "height": height},
            timeout=30,
        )
        resp.raise_for_status()
        job = resp.json()
        job_id = job.get("id") or job.get("job_id")
        if not job_id:
            return {"success": False, "error": "No job ID from Krea"}

        for _ in range(30):
            time.sleep(2)
            status_resp = requests.get(
                f"https://api.krea.ai/jobs/{job_id}",
                headers=headers, timeout=10,
            )
            status = status_resp.json()
            if status.get("status") == "completed":
                images = status.get("results", status.get("images", []))
                if images:
                    img_url = images[0].get("url") or images[0].get("image_url", "")
                    if img_url:
                        img_resp = requests.get(img_url, timeout=30)
                        with open(filepath, "wb") as f:
                            f.write(img_resp.content)
                        return {"success": True, "filepath": filepath, "method": "krea"}
                return {"success": False, "error": "No images in completed job"}
            elif status.get("status") == "failed":
                return {"success": False, "error": status.get("error", "Krea job failed")}
        return {"success": False, "error": "Krea.ai timeout (60s)"}
    except Exception as e:
        logger.warning("Krea.ai failed: %s", e)
        return {"success": False, "error": str(e)}


def _gen_pollinations(prompt: str, filepath: str,
                      width: int = 1024, height: int = 576) -> dict:
    """Generate image via Pollinations.ai (free, no API key)."""
    try:
        # Use short, clean prompt for URL — less chance of timeout
        short_prompt = prompt[:120].replace("\n", " ").strip()
        encoded = urllib.parse.quote(short_prompt)
        seed = abs(hash(prompt)) % 99999
        url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&seed={seed}"

        logger.info("Generating image via Pollinations.ai (seed=%d, %dx%d)", seed, width, height)
        resp = requests.get(url, timeout=45, stream=True)
        resp.raise_for_status()

        total = 0
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
                total += len(chunk)

        if total < 5000:
            os.remove(filepath)
            return {"success": False, "error": f"Image too small ({total} bytes)"}

        logger.info("Pollinations image saved: %d bytes", total)
        return {"success": True, "filepath": filepath, "method": "pollinations"}
    except requests.exceptions.Timeout:
        logger.warning("Pollinations timed out, falling back to picsum")
        return _gen_picsum(filepath, width, height)
    except Exception as e:
        logger.warning("Pollinations failed: %s, falling back to picsum", e)
        return _gen_picsum(filepath, width, height)


def _gen_picsum(filepath: str, width: int = 1024, height: int = 576) -> dict:
    """Fallback: get a random image from picsum.photos."""
    try:
        seed = abs(hash(filepath)) % 10000
        url = f"https://picsum.photos/seed/{seed}/{width}/{height}"
        logger.info("Generating fallback image via Picsum")
        resp = requests.get(url, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)
        if os.path.getsize(filepath) < 3000:
            os.remove(filepath)
            return {"success": False, "error": "Picsum image too small"}
        return {"success": True, "filepath": filepath, "method": "picsum"}
    except Exception as e:
        logger.warning("Picsum failed: %s", e)
        return {"success": False, "error": str(e)}


def generate_trend_image(title: str, summary: str,
                         save_dir: str | None = None,
                         model: str = "auto",
                         style: str = "auto",
                         size: str = "auto") -> dict:
    """Generate an image for a trend.
    model: 'provider/model_key', 'auto', or specific model.
    style: 'digital-art', 'realistic', 'abstract', 'neon-tech', 'minimalist', 'auto'.
    size: 'landscape', 'square', 'portrait', 'auto'.
    """
    save_dir = save_dir or Config.IMAGES_DIR
    os.makedirs(save_dir, exist_ok=True)

    prompt = _build_prompt(title, summary, style)
    width, height = IMAGE_SIZES.get(size, IMAGE_SIZES["auto"])

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(save_dir, filename)

    result = {"success": False, "error": "No model available"}

    if model != "auto":
        parts = model.split("/", 1)
        provider = parts[0] if len(parts) == 2 else "free"
        model_key = parts[1] if len(parts) == 2 else parts[0]

        if provider == "openrouter":
            result = _gen_openrouter(prompt, model_key, filepath)
        elif provider == "krea":
            result = _gen_krea(prompt, model_key, filepath, width, height)
        elif provider == "free" and model_key == "picsum":
            result = _gen_picsum(filepath, width, height)
        else:
            result = _gen_pollinations(prompt, filepath, width, height)
    else:
        # Auto: try Pollinations first (free, fast), then OpenRouter, then Krea
        result = _gen_pollinations(prompt, filepath, width, height)

        if not result.get("success") and Config.OPENROUTER_API_KEY:
            result = _gen_openrouter(prompt, "gemini-image", filepath)

        if not result.get("success") and os.getenv("KREA_API_KEY"):
            result = _gen_krea(prompt, "flux-dev", filepath, width, height)

        if not result.get("success"):
            result = _gen_picsum(filepath, width, height)

    if result.get("success"):
        result["filename"] = filename
        result["url"] = f"/static/generated/images/{filename}"
        result["prompt"] = prompt[:200]
        logger.info("Image generated: %s via %s", filename, result.get("method"))

    return result

