# -*- coding: utf-8 -*-
"""
Script  →  çoklu TTS → mp3 + srt
"""
import os
import tempfile
import logging
import ffmpeg
import openai
from dotenv import load_dotenv
from utils.media_utils import split_sentences, build_srt   # 👈
import random

# ---------- mevcut OPENAI TTS ses listesi ----------
TTS_VOICES = ["onyx", "echo", "fable", "nova", "shimmer"]

# ---------- tek cümlelik TTS ----------
def tts_segment(text: str, voice: str) -> bytes:
    logger.debug("TTS başlatılıyor | voice=%s | text='%s…'", voice, text[:40])
    resp = openai.audio.speech.create(model="tts-1", voice=voice, input=text)
    logger.debug("TTS tamamlandı | %d bayt", len(resp.content))
    return resp.content      


# ────────── LOG KURULUMU ──────────
LOG_LEVEL = os.getenv("TTS_LOG_LEVEL", "INFO").upper()   
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    level=getattr(logging, LOG_LEVEL),
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ────────── OPENAI KURULUMU ──────────
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
logger.debug("OpenAI anahtarı yüklendi, ilk 4 hane: %s****",
             openai.api_key[:4] if openai.api_key else "NONE")


# ---------- SABİT HIZ ORANI ----------
SPEED_UP_RATIO = 1.10 

def generate_audio(context: dict):
    script_path   = context["script_path"]
    audio_path    = context["audio_path"]
    subtitle_path = context["subtitle_path"]

    logger.info("Script okunuyor → %s", script_path)
    with open(script_path, encoding="utf-8") as fp:
        script = fp.read()

    sentences = split_sentences(script)
    logger.info("Cümle sayısı: %d", len(sentences))

    selected_voice = random.choice(TTS_VOICES)
    logger.info("🎙️ Seçilen ses: %s", selected_voice)

    seg_paths, seg_durs = [], []
    tmpdir = tempfile.mkdtemp(prefix="tts_seg_")
    logger.debug("Geçici klasör: %s", tmpdir)

    for idx, sent in enumerate(sentences, 1):
        seg_file = os.path.join(tmpdir, f"seg{idx:02}.mp3")
        logger.debug("Segment %02d oluşturuluyor → %s", idx, seg_file)
        with open(seg_file, "wb") as fp:
            fp.write(tts_segment(sent, voice=selected_voice))  
        dur = float(ffmpeg.probe(seg_file)["format"]["duration"])
        logger.debug("Segment %02d süresi: %.3f s", idx, dur)
        seg_paths.append(seg_file); seg_durs.append(dur)

    # --- kalan kısımlar aynı ---


    # --- concat.txt oluştur ---
    concat_txt = os.path.join(tmpdir, "list.txt")
    with open(concat_txt, "w") as f:
        for p in seg_paths:
            f.write(f"file '{p}'\n")

    combined_path = os.path.join(tmpdir, "combined.mp3")
    (
        ffmpeg
        .input(concat_txt, format="concat", safe=0)
        .output(combined_path, acodec="copy")
        .run(overwrite_output=True, quiet=LOG_LEVEL != "DEBUG")
    )

    # --- hızlandırılmış dosyayı üret ---
    if SPEED_UP_RATIO != 1.0:
        logger.info("⚡ Ses dosyası %sx hızlandırılıyor...", SPEED_UP_RATIO)
        (
            ffmpeg
            .input(combined_path)
            .filter("atempo", SPEED_UP_RATIO)
            .output(audio_path)
            .run(overwrite_output=True, quiet=LOG_LEVEL != "DEBUG")
        )
    else:
        os.rename(combined_path, audio_path)

    logger.info("✅ Ses dosyası oluşturuldu → %s", audio_path)

    # --- hızlandırılmış sürelerle altyazı oluştur ---
    adjusted_durs = [d / SPEED_UP_RATIO for d in seg_durs]
    build_srt(sentences, adjusted_durs, subtitle_path)
    logger.info("✅ Altyazı dosyası oluşturuldu → %s", subtitle_path)


# --------------- bağımsız test ---------------
if __name__ == "__main__":
    CVE = "CVE-2000-0944"
    generate_audio({
        "script_path":   f"output/scripts/{CVE}.txt",
        "audio_path":    f"output/audio/{CVE}.mp3",
        "subtitle_path": f"output/subtitles/{CVE}.srt"
    })
