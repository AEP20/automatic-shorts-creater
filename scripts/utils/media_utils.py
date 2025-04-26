# -*- coding: utf-8 -*-
"""
Ortak metin ve altyazı yardımcıları
"""
import re
from pathlib import Path

# ---------- zaman ----------
def seconds_to_timestamp(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

# ---------- metni cümlelere böl ----------
MAX_WORDS = 12
MIN_WORDS = 5

def split_sentences(text: str, max_words: int = MAX_WORDS):
    """
    Nokta / ünlem / soru işaretinden sonra büyük harf geliyorsa ayır.
    Uzun cümleleri max_words kelimelik bloklara kır.
    """
    pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    raw_sentences = re.split(pattern, text.strip())
    sentences = []

    for raw in raw_sentences:
        words = raw.split()
        while len(words) > max_words:
            sentences.append(" ".join(words[:max_words]))
            words = words[max_words:]
        if words:
            sentences.append(" ".join(words))

    # çok kısa blokları birleştir
    optimized = []
    i = 0
    while i < len(sentences):
        cur = sentences[i]
        if len(cur.split()) < MIN_WORDS and i + 1 < len(sentences):
            optimized.append(cur + " " + sentences[i + 1])
            i += 2
        else:
            optimized.append(cur)
            i += 1
    return optimized

# ---------- SRT üret ----------
def build_srt(sentences, durations, srt_path: str):
    Path(srt_path).parent.mkdir(parents=True, exist_ok=True)
    cursor = 0.0
    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, (sent, dur) in enumerate(zip(sentences, durations), start=1):
            start = seconds_to_timestamp(cursor)
            end   = seconds_to_timestamp(cursor + dur)
            f.write(f"{idx}\n{start} --> {end}\n{sent}\n\n")
            cursor += dur
    print(f"✅ SRT senkron tamamlandı → {srt_path}")
