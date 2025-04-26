# -*- coding: utf-8 -*-
"""
Dikey (1080×1920, 30 fps) Shorts arka planı üretir,
üstüne altyazı ve sesi bind eder.
Hata kontrolleri ve güvenli dosya işlemleri eklendi.
"""
import os
import random
import logging
import ffmpeg

# ----------  AYARLAR  ----------
TARGET_W, TARGET_H, TARGET_FPS = 1080, 1920, 30
CROSSFADE = 0.5                     # sn
BG_DIR     = "assets/backgrounds"
TMP_DIR    = "temp"
TMP_BG     = os.path.join(TMP_DIR, "temp_background.mp4")

SPEED_FACTOR = 0.70

STYLE = (
    "FontName=Arial,"
    "FontSize=12,"
    "PrimaryColour=&HFFFFFF&,"      # Beyaz yazı
    "OutlineColour=&H000000&,"       # Siyah kenar çizgisi
    "BorderStyle=1,"                 # Kenar çizgili stil
    "Outline=1,"                     # Kenar kalınlığı
    "Shadow=1,"                      # Gölge
    "Bold=1,"                        # Kalın yazı
    "Alignment=2,"                   # Ortalanmış yazı
    "MarginL=40,"                    # Soldan boşluk
    "MarginR=40,"                    # Sağdan boşluk
    "MarginV=50,"                    # Alttan boşluk
)

LOG_LEVEL = os.getenv("VIDEO_LOG_LEVEL", "INFO").upper()
logging.basicConfig(format="%(asctime)s | %(levelname)-8s | %(message)s",
                    level=getattr(logging, LOG_LEVEL), datefmt="%H:%M:%S")
logger = logging.getLogger("video_pipeline")


# ----------  YARDIMCI FONKSİYONLAR  ----------
def _probe_duration(path: str) -> float:
    try:
        return float(ffmpeg.probe(path)["format"]["duration"])
    except Exception as exc:
        raise RuntimeError(f"🛑 {path} süresi okunamadı: {exc}") from exc


def _prepare_clip(path: str, seg_dur: float, speed: float = 1.0):
    """
    Klibi ölçekler, FPS sabitler ve speed faktörü uygular.
    Son çıktının süresi tam seg_dur olur.
    """
    real_dur = _probe_duration(path)

    inp = ffmpeg.input(path, ss=0)

    # Hız / yavaşlat
    if abs(speed - 1.0) > 1e-3:
        inp = inp.filter("setpts", f"PTS/{speed}")
        real_dur *= (1 / speed)   # yavaşlatınca süre uzar, hızlandırınca kısalır

    # speed sonrası gereken ham süre
    raw_needed = seg_dur
    # Eğer videonun süresi yetmiyorsa loop yap
    if real_dur < raw_needed - 0.1:
        loop_cnt = int(raw_needed // real_dur) + 1
        inp = inp.filter_multi_output(
            "loop", loop=loop_cnt, size=int(real_dur * TARGET_FPS)
        )[0]
        logger.debug(f"🔄 {path} döngüyle {loop_cnt}× uzatıldı")

    # Kes, ölçekle, fps sabitle
    inp = (inp.trim(start=0, end=raw_needed)
               .filter("setpts", "PTS-STARTPTS")    # trim sonrası timestamp sıfırla
               .filter("scale", TARGET_W, TARGET_H)
               .filter("fps", TARGET_FPS, round="up"))

    # Renk uyumluluğu
    return inp.filter("format", "yuv420p")

def _build_xfade_chain(clips, seg_dur):
    """
    clip[0] ⭢ clip[1] ⭢ …  zinciri, her adımda
    offset = k*(seg_dur - CROSSFADE) formülüyle kurulur.
    """
    out = clips[0]
    offset = seg_dur - CROSSFADE          # ilk geçiş başlangıcı

    for nxt in clips[1:]:
        out = ffmpeg.filter(
            [out, nxt], "xfade",
            transition="fade",
            duration=CROSSFADE,
            offset=offset
        )
        offset += seg_dur - CROSSFADE     # sonraki geçişin başlangıcı

    return out


# ----------  ANA İŞLEVLER  ----------
def create_combined_background(total_dur: float) -> None:
    os.makedirs(TMP_DIR, exist_ok=True)

    bg_files = [os.path.join(BG_DIR, f) for f in os.listdir(BG_DIR) if f.endswith(".mp4")]
    if len(bg_files) < 3:
        raise RuntimeError("🛑 En az 3 arka plan videosu gerekli!")

    chosen = random.sample(sorted(bg_files), 3)
    seg_dur = total_dur / 3
    logger.info(f"🎬 Seçilen videolar: {chosen}  (her biri ≈ {seg_dur:.2f}s)")

    clips = [_prepare_clip(p, seg_dur) for p in chosen]
    background = _build_xfade_chain(clips, seg_dur)

    (ffmpeg
     .output(background, TMP_BG,
             vcodec="libx264", crf=18, preset="fast",
             pix_fmt="yuv420p", movflags="faststart")
     .overwrite_output()
     .run(quiet=LOG_LEVEL != "DEBUG"))
    logger.info(f"✅ Temp background hazır: {TMP_BG}")


def generate_video(ctx: dict) -> None:
    """
    ctx = {
        "audio_path": "...mp3",
        "subtitle_path": "...srt",
        "video_path": "...mp4"
    }
    """
    audio_path, sub_path, out_path = (ctx[k] for k in ("audio_path",
                                                      "subtitle_path",
                                                      "video_path"))
    if not all(map(os.path.exists, (audio_path, sub_path))):
        raise FileNotFoundError("🛑 Ses ya da altyazı dosyası bulunamadı!")

    duration = _probe_duration(audio_path)
    logger.info(f"🔊 Ses süresi: {duration:.2f}s")

    if duration > 60:
        raise ValueError("🛑 Ses süresi 1 dakikadan fazla olamaz!")

    create_combined_background(duration)

    video_bg = ffmpeg.input(TMP_BG)
    video_bg = ffmpeg.filter(video_bg, "subtitles", sub_path, force_style=STYLE)
    audio_in = ffmpeg.input(audio_path)

    logger.info("📦 Görüntü + ses mux ediliyor…")
    (ffmpeg
     .output(video_bg, audio_in, out_path,
             t=duration + 0.1,
             vcodec="libx264", acodec="aac", crf=18,
             preset="slow", movflags="faststart")
     .overwrite_output()
     .run(quiet=LOG_LEVEL != "DEBUG"))
    logger.info(f"🏁 Bitti: {out_path}")

    try:
        os.remove(TMP_BG)
        logger.debug("🧹 Temp silindi")
    except OSError as e:
        logger.warning(f"⚠️ Temp silinemedi: {e}")


# ---------------  ÖRNEK ÇALIŞTIRMA ---------------
if __name__ == "__main__":
    example_cve = "CVE-2001-0766"
    generate_video({
        "audio_path": f"output/audio/{example_cve}.mp3",
        "subtitle_path": f"output/subtitles/{example_cve}.srt",
        "video_path": f"output/videos/{example_cve}.mp4",
    })