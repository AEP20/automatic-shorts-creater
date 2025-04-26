import random
import requests
import json
from datetime import datetime
import time

NVD_SINGLE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={}"

# =======================
# Enrichment Functions
# =======================

def enrich_attack_vector(cve_data):
    try:
        return cve_data["metrics"]["cvssMetricV31"][0]["cvssData"]["attackVector"]
    except:
        return None

def enrich_user_interaction(cve_data):
    try:
        return cve_data["metrics"]["cvssMetricV31"][0]["cvssData"]["userInteraction"]
    except:
        return None

def enrich_privileges_required(cve_data):
    try:
        return cve_data["metrics"]["cvssMetricV31"][0]["cvssData"]["privilegesRequired"]
    except:
        return None

def enrich_cwe_info(cve_data):
    try:
        weaknesses = cve_data.get("weaknesses", [])
        if weaknesses and "description" in weaknesses[0]:
            descs = weaknesses[0]["description"]
            if descs:
                return {
                    "cwe_id": weaknesses[0]["source"],
                    "cwe_name": descs[0]["value"]
                }
    except:
        pass
    return {}

def enrich_tags(description):
    tags = []
    desc = description.lower()

    keywords = {
        "buffer overflow": "buffer_overflow",
        "brute force": "brute_force",
        "sql injection": "sql_injection",
        "cross site scripting": "xss",
        "arbitrary code": "rce",
        "dns spoof": "dns_spoofing",
        "authentication bypass": "auth_bypass",
        "double free": "double_free",
        "heap overflow": "heap_overflow"
    }

    for kw, tag in keywords.items():
        if kw in desc:
            tags.append(tag)

    return tags

# =======================
# Main Fetch + Enrich
# =======================

def get_detailed_cve(cve_id):
    url = NVD_SINGLE_URL.format(cve_id)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
    }
    print(f"🔎 Fetching details for {cve_id}...")
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        vuln_list = data.get("vulnerabilities", [])
        if vuln_list:
            print(f"✅ Found details for {cve_id}")
            return vuln_list[0]["cve"]
        else:
            print(f"⚠️ No vulnerability data found for {cve_id}")
    else:
        print(f"❌ Failed to fetch {cve_id} (status code {res.status_code})")
    return None


def main():
    print("🚀 Başlıyoruz: Kritik CVE'leri çekiyoruz...")
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0?cvssV3Severity=CRITICAL&resultsPerPage=20"
    res = requests.get(url)
    data = res.json()

    try:
        with open("data/filtered_cves.json", "r") as f:
            existing = json.load(f)
    except:
        existing = []

    used_ids = set([item["id"] for item in existing])
    new_cves = []

    for item in data.get("vulnerabilities", []):
        cve_meta = item["cve"]
        cve_id = cve_meta["id"]
        desc = cve_meta["descriptions"][0]["value"]
        score = cve_meta["metrics"]["cvssMetricV31"][0]["cvssData"]["baseScore"]

        print(f"\n➡️  İşleniyor: {cve_id}")

        if cve_id in used_ids:
            print("⏭️ Zaten mevcut, atlanıyor.")
            continue
        if score < 8.0:
            print("🔻 Skor düşük (<8.0), atlanıyor.")
            continue

        detailed_cve = get_detailed_cve(cve_id)
        if not detailed_cve:
            print("❌ Detay alınamadı, geçildi.")
            continue

        time.sleep(random.uniform(5.0, 10.0))

        # year = int(cve_id.split("-")[1])
        # if year < 2005:
        #     print("⏮️ CVE çok eski (<2005), atlanıyor.")
        #     continue


        cve_obj = {
            "id": cve_id,
            "score": score,
            "description": desc,
            "source": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            "date_added": str(datetime.utcnow()),
            "attack_vector": enrich_attack_vector(detailed_cve),
            "user_interaction": enrich_user_interaction(detailed_cve),
            "privileges_required": enrich_privileges_required(detailed_cve),
            "tags": enrich_tags(desc)
        }

        cwe_info = enrich_cwe_info(detailed_cve)
        cve_obj.update(cwe_info)

        print(f"✅ {cve_id} başarıyla eklendi.")
        new_cves.append(cve_obj)

    with open("data/filtered_cves.json", "w") as f:
        json.dump(existing + new_cves, f, indent=2)

    print(f"\n🎉 Tamamlandı! {len(new_cves)} yeni CVE eklendi ve zenginleştirildi.")

if __name__ == "__main__":
    main()
