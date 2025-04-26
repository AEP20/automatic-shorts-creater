# scripts/generate_script.py

import json
import os
from dotenv import load_dotenv
from openai import OpenAI

LANGUAGE = "en"  

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print("🔑 OpenAI API anahtarı yüklendi :", os.getenv("OPENAI_API_KEY")[:4] + "****")

def load_cves(filepath="data/filtered_cves.json"):
    print(f"📂 CVE verileri okunuyor: {filepath}")
    with open(filepath, "r") as f:
        data = json.load(f)
    print(f"✅ {len(data)} adet CVE yüklendi.")
    return data

def select_random_cve(cves):
    print("🎯 Kullanılmamış CVE seçiliyor...")
    unused = [cve for cve in cves if not cve.get("used")]
    if not unused:
        print("🚫 Kullanılmamış CVE kalmadı.")
        return None
    selected = unused[0]
    print(f"🎯 Seçilen CVE: {selected['id']}")
    return selected

def generate_prompt(cve):
    print(f"🧠 Prompt hazırlanıyor: {cve['id']}")
    tags_formatted = ", ".join(cve.get("tags", [])) or "none"

    if LANGUAGE == "tr":
        return f"""
Sen uzman bir YouTube Shorts senaryo yazarı olarak çalışıyorsun ve siber güvenlik açıklarını etkileyici, kolay anlaşılır şekilde anlatıyorsun.

Görevin:
40–50 saniyelik bir YouTube Shorts için yaklaşık **200–220 kelimelik** bir konuşma senaryosu yazmak.

Senaryoyu 5 bölüme ayır:
1. **İLGİ ÇEKİCİ AÇILIŞ** (1 cümle)
2. **NE OLDU** (3–4 cümle)
3. **NASIL SÖMÜRÜLDÜ** (3–4 cümle)
4. **NEDEN ÖNEMLİ** (3–4 cümle)
5. **ÇAĞRI** – abone ol, takip et gibi.

Ton: Gerilimli, canlı ve doğal.  
Teknik terimler (örneğin: Buffer Overflow, RCE, CVE ID) İngilizce kalsın ancak **Türkçe cümlelerle** açık ve sade bir dil kullanarak anlatım yap.

CVE Bilgileri:
- CVE Kimliği: {cve['id']}  
- Açıklama: {cve['description']}
- Saldırı Vektörü: {cve.get('attack_vector', 'Bilinmiyor')}
- Gerekli Ayrıcalıklar: {cve.get('privileges_required', 'Bilinmiyor')}
- Kullanıcı Etkileşimi: {cve.get('user_interaction', 'Bilinmiyor')}
- CWE Kategorisi: {cve.get('cwe_name', 'Bilinmiyor')}
- Etiketler: {tags_formatted}

Çıktı: SADECE KONUŞMA METNİNİ OLUŞTUR. Başlık, etiket, açıklama vs. ekleme. Çünkü direkt seslendirme yapılacak.
"""
    else: 
        return f"""
You are an expert YouTube Shorts scriptwriter crafting punchy, high-retention cybersecurity explainers.

Your task:
Write a spoken YouTube Shorts script (target 180–200 words) for a voiceover lasting **35 to 45 seconds**.

Structure:
- **Start with a strong HOOK** (don't always begin with "Imagine"; vary the opening styles).
- **Briefly explain WHAT HAPPENED** (avoid deep technical terms unless explained in 1 short sentence).
- **Describe HOW IT WAS EXPLOITED** (keep it vivid and dramatic, highlight the attack simplicity if possible).
- **Emphasize WHY IT MATTERS** (mention real-world impact if relevant, even hypothetically if needed).
- **End with a dynamic CTA** (vary expressions: like, comment, follow, stay tuned, etc.).

Tone: Suspenseful, vivid, and easy to understand. 
Avoid technical jargon unless explained very briefly.

CVE Details:
- CVE ID: {cve['id']}  
- Description: {cve['description']}
- Attack Vector: {cve.get('attack_vector', 'N/A')}
- Privileges Required: {cve.get('privileges_required', 'N/A')}
- User Interaction: {cve.get('user_interaction', 'N/A')}
- CWE Category: {cve.get('cwe_name', 'N/A')}
- Tags: {tags_formatted}

Output: Only the spoken script, no section labels, no extra formatting.
"""


def generate_script(cve, context):
    prompt = generate_prompt(cve)
    print("📡 GPT-4'e istek gönderiliyor...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who writes YouTube Shorts scripts."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=400
    )
    script_text = response.choices[0].message.content
    print("✅ Script başarıyla oluşturuldu.")

    os.makedirs(os.path.dirname(context["script_path"]), exist_ok=True)
    with open(context["script_path"], "w") as f:
        f.write(script_text)
    print(f"💾 Script dosyaya yazıldı: {context['script_path']}")

# 🧪 Test bloğu
if __name__ == "__main__":
    cves = load_cves()
    cve = select_random_cve(cves)

    if not cve:
        exit()

    context = {
        "script_path": f"output/scripts/{cve['id']}.txt"
    }

    generate_script(cve, context)

    cve["used"] = True
    with open("data/filtered_cves.json", "w") as f:
        json.dump(cves, f, indent=2)
