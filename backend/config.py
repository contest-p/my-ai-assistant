import json
import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

# .env 파일을 읽어서 os.environ에 채워 넣습니다.
# 배포 환경(Render)에서는 .env 파일이 없고 대시보드에 등록한 환경변수를 바로 쓰므로,
# load_dotenv()는 로컬 개발 환경에서만 실질적인 역할을 합니다.
load_dotenv()


def _parse_origins(raw: str) -> list[str]:
    raw = (raw or "*").strip()
    if raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


# CORS 허용 도메인. 개발 중엔 .env에서 안 정해줘도 "*"로 동작합니다.
# Phase 9(배포)에서 실제 Vercel 도메인으로 좁힙니다 (PRD 26번).
ALLOWED_ORIGINS = _parse_origins(os.getenv("ALLOWED_ORIGINS", "*"))

# Phase 6(AI 챗봇)에서 실제로 읽어서 사용하기 시작합니다.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# 코디세이 프록시 엔드포인트. OpenAI 클라이언트 생성 시 base_url로 넘겨야 합니다
# (안 넘기면 기본값인 api.openai.com으로 요청이 나가서 sk-cody-live- 키가 안 먹힘).
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

# Firebase Admin SDK 초기화.
# FIREBASE_SERVICE_ACCOUNT_JSON은 서비스 계정 키 JSON 파일의 "내용"을 문자열로 담은
# 환경변수다 (파일 경로가 아님 — Render 같은 배포 환경엔 파일을 올리지 않으므로).
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if not FIREBASE_SERVICE_ACCOUNT_JSON:
    raise RuntimeError(
        "FIREBASE_SERVICE_ACCOUNT_JSON 환경변수가 설정되지 않았습니다. "
        ".env(로컬) 또는 Render 대시보드(배포)에 등록했는지 확인하세요."
    )

if not firebase_admin._apps:
    _cred = credentials.Certificate(json.loads(FIREBASE_SERVICE_ACCOUNT_JSON))
    firebase_admin.initialize_app(_cred)

# 다른 모듈(routers/services/scripts)은 여기서 db를 가져다 쓴다.
db = firestore.client()
