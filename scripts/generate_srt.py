import os
import re
from utils.utils import highlight_keywords

MIN_WORDS_PER_BLOCK = 5
MAX_WORDS_PER_BLOCK = 12
MIN_DURATION = 1.5  

def seconds_to_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def split_sentences(text: str):
    pattern = r'(?<=[.?!])\s+(?=[A-Z])'
    raw_sentences = re.split(pattern, text)
    sentences = []

    for raw in raw_sentences:
        words = raw.strip().split()
        while len(words) > MAX_WORDS_PER_BLOCK:
            sentences.append(' '.join(words[:MAX_WORDS_PER_BLOCK]))
            words = words[MAX_WORDS_PER_BLOCK:]
        if words:
            sentences.append(' '.join(words))

    optimized = []
    i = 0
    while i < len(sentences):
        current = sentences[i]
        if len(current.split()) < MIN_WORDS_PER_BLOCK and i + 1 < len(sentences):
            merged = current + ' ' + sentences[i + 1]
            optimized.append(merged)
            i += 2
        else:
            optimized.append(current)
            i += 1

    return optimized

def generate_srt(script_path: str, srt_path: str, duration: float):
    with open(script_path, "r") as f:
        raw_text = f.read()

    sentences = split_sentences(raw_text)
    total_words = sum(len(s.split()) for s in sentences)

    if total_words == 0:
        print("⚠️ Script boş veya işlenemiyor.")
        return

    with open(srt_path, "w") as f:
        time_cursor = 0.0
        for i, sentence in enumerate(sentences):
            word_count = len(sentence.split())
            chunk_duration = max((word_count / total_words) * duration, MIN_DURATION)

            start = seconds_to_timestamp(time_cursor)
            end = seconds_to_timestamp(time_cursor + chunk_duration)

            colored_sentence = highlight_keywords(sentence.strip()) 
            f.write(f"{i + 1}\n{start} --> {end}\n{colored_sentence}\n\n")

            time_cursor += chunk_duration

    print(f"✅ Optimize altyazı oluşturuldu: {srt_path}")


# Test
if __name__ == "__main__":
    CVE_ID = "CVE-2000-0944"
    SCRIPT_PATH = f"output/scripts/{CVE_ID}.txt"
    SRT_PATH = f"output/subtitles/{CVE_ID}.srt"
    DURATION = 60.0 

    os.makedirs(os.path.dirname(SRT_PATH), exist_ok=True)
    generate_srt(SCRIPT_PATH, SRT_PATH, DURATION)
