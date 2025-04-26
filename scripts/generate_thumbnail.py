# scripts/generate_thumbnail.py

# -*- coding: utf-8 -*-
import os
import logging
import base64
from dotenv import load_dotenv
from openai import OpenAI
from utils.utils import resize_image_to_16_9
from PIL import Image  # 👈 Ekledik
import io
import random

# ───── LOGGING SETUP ─────
LOG_LEVEL = os.getenv("THUMBNAIL_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=getattr(logging, LOG_LEVEL),
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ───── OPENAI CLIENT ─────
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger.debug("OpenAI API anahtarı yüklendi: %s****", os.getenv("OPENAI_API_KEY")[:4])

# ───── THUMBNAIL ÜRETİCİ ─────
def generate_thumbnail(context: dict):
    prompt = build_dynamic_prompt(context["cve_id"], tags=context.get("tags", []))
    output_path = context["output_path"]
    logger.info("🎨 Thumbnail üretimi başlatıldı")
    logger.debug("Prompt: %s", prompt)

    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1536",
            n=1,
            quality="medium",
        )

        image_data = response.data[0]
        b64_image = image_data.b64_json

        if not b64_image:
            logger.error("❌ Görsel base64 verisi alınamadı.")
            return

        img_bytes = base64.b64decode(b64_image)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_bytes)

        logger.info("💾 Görsel kaydedildi → %s", output_path)

        resize_image_to_16_9(output_path, output_path.replace("_thumb", "_thumb_720"))

        # 🔥 Boyutu optimize et
        optimize_thumbnail_size(output_path.replace("_thumb", "_thumb_720"))

    except Exception as e:
        logger.error("❌ Görsel üretiminde hata: %s", str(e))

# ───── THUMBNAIL OPTİMİZE EDİCİ ─────
def optimize_thumbnail_size(image_path: str):
    MAX_SIZE = 2 * 1024 * 1024  # 2MB

    if not os.path.exists(image_path):
        logger.error(f"❌ Optimize edilecek dosya bulunamadı: {image_path}")
        return

    size = os.path.getsize(image_path)
    logger.info(f"📦 Başlangıç dosya boyutu: {size / 1024:.2f} KB")

    if size <= MAX_SIZE:
        logger.info("✅ Görsel zaten 2MB altında, sıkıştırmaya gerek yok.")
        return

    try:
        img = Image.open(image_path)
        quality = 95

        while size > MAX_SIZE and quality > 10:
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
            new_size = buffer.tell()

            logger.debug(f"🔄 Dene: Quality={quality}, Boyut={new_size / 1024:.2f} KB")

            if new_size <= MAX_SIZE:
                with open(image_path, "wb") as f:
                    f.write(buffer.getvalue())
                logger.info(f"✅ Sıkıştırma başarılı: {new_size / 1024:.2f} KB ile Quality={quality}")
                return

            quality -= 5  # her seferinde %5 azaltıyoruz

        logger.warning("⚠️ Maksimum sıkıştırmaya rağmen 2MB altına inilemedi.")

    except Exception as e:
        logger.error(f"❌ Optimize etme hatası: {e}")

# ───── PROMPT OLUŞTURUCU ─────
def build_dynamic_prompt(cve_id: str, tags: list[str] = None) -> str:
    layout = random.choice([
        "professional YouTube thumbnail",
        "clean graphic layout for YouTube Shorts",
        "high-contrast YouTube video cover design",
        "bold and readable YouTube thumbnail"
    ])
    
    theme = random.choice([
        "dark background with red highlights",
        "glitch effect with neon colors",
        "black UI with glowing blue text",
        "minimal tech-style layout with digital accents"
    ])
    
    element = random.choice([
        "a person in a hooded jacket",
        "a terminal-style interface window",
        "a glowing padlock",
        "a warning popup",
        "an alert screen with code lines"
    ])
    
    prompt = (
        f"{layout} for a cybersecurity video titled '{cve_id}'. "
        f"Use {theme}, include {element}. "
        f"Design must be readable at small sizes and optimized for YouTube Shorts. "
        f"This is for educational and informational purposes about digital risks and awareness."
    )

    if tags:
        tags_text = " ".join(tags).lower()
        if "rce" in tags_text:
            prompt += " Suggest a digital shell or abstract system diagram."
        if "xss" in tags_text:
            prompt += " Include a browser-like frame with code overlay."
        if "auth" in tags_text:
            prompt += " Use login-related visuals or a padlock symbol."
        if "zero-day" in tags_text:
            prompt += " Overlay 'ZERO-DAY' in bold red with subtle glitch effect."

    logger.info("Dinamik oluşturulan prompt: %s", prompt)
    return prompt

# ───── TEST BLOĞU ─────
if __name__ == "__main__":
    context = {
        "cve_id": "CVE-2001-0766",
        "tags": ["rce", "xss", "auth"]
    }
    output_path = f"output/thumbnails/{context['cve_id']}_thumb.png"
    context["output_path"] = output_path

    generate_thumbnail(context)
