# scripts/utils/context.py

import os

def create_context(cve: dict) -> dict:
    cve_id = cve["id"]
    return {
        "cve_id": cve_id,
        "script_path":     f"output/scripts/{cve_id}.txt",
        "audio_path":      f"output/audio/{cve_id}.mp3",
        "subtitle_path":   f"output/subtitles/{cve_id}.srt",
        "video_path":      f"output/videos/{cve_id}.mp4",
        "output_path":     f"output/thumbnails/{cve_id}_thumb.png",  # thumbnail
        "background_video": "assets/backgrounds/cyber_video_02.mp4",  # default background
        "tags": cve.get("tags", []),  # ✅ Artık gerçek tag'ler,
        "thumbnail_path": f"output/thumbnails/{cve_id}_thumb_720.png",
        "caption_path":    f"output/captions/{cve_id}.txt",
    }
