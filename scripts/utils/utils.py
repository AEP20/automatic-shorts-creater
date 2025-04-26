import re, textwrap
from PIL import Image

def split_sentences(text, max_words=12):
    pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    raw = re.split(pattern, textwrap.dedent(text).strip())
    out = []
    for s in raw:
        words = s.split()
        while len(words) > max_words:
            out.append(' '.join(words[:max_words]))
            words = words[max_words:]
        if words:
            out.append(' '.join(words))
    return out

def seconds_to_timestamp(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def build_srt(sentences, durations, srt_path):
    cursor = 0.0
    with open(srt_path, "w") as f:
        for i, (sent, dur) in enumerate(zip(sentences, durations), 1):
            start = seconds_to_timestamp(cursor)
            end   = seconds_to_timestamp(cursor + dur)
            f.write(f"{i}\n{start} --> {end}\n{sent}\n\n")
            cursor += dur
    print("✅ SRT senkron tamam:", srt_path)

from PIL import Image

def resize_image_to_16_9(input_path: str, output_path: str, target_size=(1080, 1920)):
    with Image.open(input_path) as img:
        resized = img.resize(target_size, Image.Resampling.LANCZOS)
        resized.save(output_path)
        print(f"🔧 Görsel yeniden boyutlandırıldı → {output_path}")

COLOR_PRIORITY = {
    "critical": "red",
    "vulnerability": "red",
    "attack": "red",
    "breach": "red",
    "exploit": "red",
    "malicious": "orange",
    "hackers": "orange",
    "remote": "orange",
    "bypass": "orange",
    "seize": "orange",
    "infiltrate": "orange",
    "compromise": "orange",
    "password": "blue",
    "security": "blue",
    "arbitrary code": "blue",
    "buffer overflow": "blue",
}

def highlight_keywords(sentence: str) -> str:
    COLORS = {
        "red": r"{\c&H0000FF&}",      # Kırmızı
        "orange": r"{\c&H007FFF&}",   # Turuncu
        "blue": r"{\c&HFF8000&}",     # Mavi
    }
    for keyword, color in COLOR_PRIORITY.items():
        pattern = r'\b' + re.escape(keyword) + r'\b'  # tam kelime eşleşmesi
        print(f"Word found: {keyword}")
        colored = COLORS[color] + keyword + r"{\c}"  # doğru renkle kapla
        sentence = re.sub(pattern, colored, sentence, flags=re.IGNORECASE)
    return sentence
