import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

# --- Config
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

LOG_LEVEL = os.getenv("CAPTION_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=getattr(logging, LOG_LEVEL),
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

def generate_captions(cve, context):
    """
    Generates an action-driven, slightly dramatic English title and description without labels.
    """
    logger.info("📝 Captions generation started...")
    
    prompt = f"""
Create a short, dramatic YouTube Shorts caption for the following CVE:

- CVE ID: {cve['id']}
- Summary: {cve['description']}
- Category: {cve.get('cwe_name', 'N/A')}
- Tags: {", ".join(cve.get('tags', [])) if cve.get('tags') else "none"}

Instructions:
- First line: Short punchy title (do not add an emoji).
- Second line: 1-2 short sentences as description.
- Encourage viewers to think it's still dangerous or unresolved (e.g., "Is it still exploitable? 👀" or "Stay alert! 🚨").
- DO NOT write labels like "Title:" or "Description:".
- Keep it natural and captivating.
- Limit to ~60 words total.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a copywriter specialized in cybersecurity YouTube Shorts."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=140
    )

    caption_text = response.choices[0].message.content.strip()
    
    os.makedirs(os.path.dirname(context["caption_path"]), exist_ok=True)
    with open(context["caption_path"], "w", encoding="utf-8") as f:
        f.write(caption_text)
    
    logger.info("✅ Captions successfully generated: %s", context["caption_path"])

# 🧪 For standalone testing
if __name__ == "__main__":
    CVE_ID = "CVE-2001-0766"
    fake_cve = {
        "id": CVE_ID,
        "description": "The decompression algorithm in zlib allows remote attackers to cause denial of service or execute arbitrary code.",
        "cwe_name": "CVE-2001-0766",
        "tags": ["rce", "double_free", "memory_corruption"]
    }
    context = {
        "caption_path": f"output/captions/{CVE_ID}.txt"
    }
    generate_captions(fake_cve, context)
