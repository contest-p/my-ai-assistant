import os

from dotenv import load_dotenv

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

# 아래 세 값은 아직 Phase 1에서는 안 씁니다.
# Phase 2(Firestore 연동)와 Phase 6(AI 챗봇)에서 실제로 읽어서 사용하기 시작합니다.
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
