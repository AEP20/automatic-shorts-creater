import os
import logging
import ffmpeg  
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from youtube_scripts.youtube_authenticate import authenticate_youtube

# ───── LOGGING SETUP ─────
youtube_logger = logging.getLogger("youtube_upload")
youtube_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)
youtube_logger.addHandler(handler)

# ───── HELPER: Video Süresi Öğren ─────
def get_video_duration(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        youtube_logger.error(f"❌ Video süresi okunamadı: {e}")
        return None

# ───── ANA YÜKLEME FONKSİYONU ─────
def upload_video(context, _CVE_ID):
    youtube_logger.debug("▶️ upload_video fonksiyonu başlatıldı.")

    creds = authenticate_youtube()
    youtube_logger.debug("✅ YouTube kimlik doğrulaması tamamlandı.")

    youtube = build("youtube", "v3", credentials=creds)
    youtube_logger.debug("✅ YouTube API servisi oluşturuldu.")

    CVE_ID = _CVE_ID
    video_file = context["video_path"]
    caption_file = context["caption_path"]
    thumbnail_file = context.get("thumbnail_path")

    youtube_logger.debug(f"📁 Video dosya yolu: {video_file}")
    youtube_logger.debug(f"📄 Caption dosya yolu: {caption_file}")
    youtube_logger.debug(f"🖼️ Thumbnail dosya yolu: {thumbnail_file}")

    duration = get_video_duration(video_file)
    if duration is None:
        youtube_logger.error("❌ Video süresi alınamadı, işlem iptal.")
        return
    if duration > 60:
        youtube_logger.error(f"❌ Video {duration:.2f} saniye, Shorts olamaz. İşlem iptal edildi.")
        return
    youtube_logger.info(f"⏱️ Video süresi: {duration:.2f} saniye (Shorts için uygun)")

    try:
        with open(caption_file, "r", encoding="utf-8") as f:
            caption_text = f.read().strip()
        youtube_logger.debug("✅ Caption dosyası başarıyla okundu.")
    except Exception as e:
        youtube_logger.error(f"❌ Caption dosyası okunamadı: {e}")
        return

    lines = caption_text.splitlines()
    title = lines[0] if lines else f"Cybersecurity Short - {CVE_ID}"
    description = "\n".join(lines[1:]) if len(lines) > 1 else "Auto-generated cybersecurity shorts."

    if "#shorts" not in description.lower():
        description += "\n\n#shorts"

    youtube_logger.info(f"🔢 Title: {title}")
    youtube_logger.info(f"📄 Description: {description[:50]}...")

    try:
        media = MediaFileUpload(video_file, resumable=True, mimetype="video/*")
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": context.get("tags", []),
                    "categoryId": "28" 
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=media
        )
        youtube_logger.info("🚀 Video yükleniyor...")
        response = request.execute()
        youtube_logger.info(f"✅ Video başarıyla yüklendi! Video ID: {response['id']}")
        youtube_logger.info(f"📹 URL: https://www.youtube.com/watch?v={response['id']}")
        video_id = response["id"]
    except Exception as e:
        youtube_logger.error(f"❌ Video yükleme sırasında hata oluştu: {e}")
        return

    if thumbnail_file and os.path.exists(thumbnail_file):
        try:
            youtube_logger.info("🖼️ Thumbnail yükleniyor...")
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_file, mimetype="image/png")
            ).execute()
            youtube_logger.info("✅ Thumbnail başarıyla eklendi.")
        except Exception as e:
            youtube_logger.error(f"❌ Thumbnail yüklenemedi: {e}")
    else:
        youtube_logger.warning("⚠️ Thumbnail dosyası bulunamadı, yükleme atlandı.")

if __name__ == "__main__":
    CVE_ID = "CVE-2001-0766"
    context = {
        "id": CVE_ID,
        "video_path": f"output/videos/{CVE_ID}.mp4",
        "caption_path": f"output/captions/{CVE_ID}.txt",
        "thumbnail_path": f"output/thumbnails/{CVE_ID}_thumb_720.png",
        "tags": ["cybersecurity", "cve", "hacking", "tech"]
    }
    upload_video(context)
