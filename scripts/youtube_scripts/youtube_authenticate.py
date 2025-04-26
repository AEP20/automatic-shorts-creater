import os
import json
import logging
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube"  
]

CREDENTIALS_FILE = "scripts/youtube_scripts/credentials.json"   
TOKEN_FILE = "scripts/youtube_scripts/token.json"

def authenticate_youtube():
    creds = None

    # 1. Daha önce kayıtlı token var mı?
    if os.path.exists(TOKEN_FILE):
        logger.info("📄 Mevcut token bulundu, yükleniyor...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # 2. Token yoksa veya süresi dolmuşsa
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("🔄 Token süresi dolmuş, yenileniyor...")
            creds.refresh(Request())
        else:
            logger.info("🌐 İlk giriş yapılıyor, tarayıcı açılacak...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # 3. Tokenı kaydet
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        logger.info("✅ Token kaydedildi: %s", TOKEN_FILE)

    logger.info("🔗 YouTube API bağlantısı başarılı!")
    return creds

# Bağımsız test
if __name__ == "__main__":
    authenticate_youtube()
