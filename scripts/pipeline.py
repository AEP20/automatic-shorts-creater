import json
from generate_script import generate_script, load_cves, select_random_cve
from generate_audio import generate_audio  # ⚡ Ses hızlandırma burada yapılır
from generate_video import generate_video
from generate_thumbnail import generate_thumbnail
from utils.context import create_context
from generate_caption import generate_captions
from youtube_scripts.upload_video import upload_video


def mark_cve_used(cves, target_id):
    for cve in cves:
        if cve["id"] == target_id:
            cve["used"] = True
    with open("data/filtered_cves.json", "w") as f:
        json.dump(cves, f, indent=2)


def main():
    print("🚀 Pipeline başlatıldı!")

    # 1. CVE seç
    cves = load_cves()
    cve = select_random_cve(cves)
    if not cve:
        print("❌ Kullanılabilir CVE bulunamadı.")
        return

    cve_id = cve["id"]
    context = create_context(cve)
    print(f"📜 Seçilen CVE: {cve_id}")

    generate_script(cve, context)
    print(f"📝 Script oluşturuldu: {context['script_path']}")

    generate_audio(context)
    print(f"🔊 Ses dosyası oluşturuldu: {context['audio_path']}")

    generate_video(context)
    print(f"🎥 Video oluşturuldu: {context['video_path']}")

    generate_thumbnail(context)
    print(f"🖼️ Thumbnail oluşturuldu: {context['thumbnail_path']}")

    generate_captions(cve, context)
    print(f"📝 Altyazı dosyası oluşturuldu: {context['caption_path']}")

    mark_cve_used(cves, cve_id)
    print(f"✅ CVE işaretlendi: {cve_id}")

    upload_video(context, cve_id)

    print("✅ Pipeline başarıyla tamamlandı.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Pipeline bir hata nedeniyle durdu: {e}")

