from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers import data

app = FastAPI(title="전역 후 1년, 내 소비를 아는 AI 비서")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    """헬스체크. 배포 후 서버가 살아있는지 확인용."""
    return {"status": "ok"}


app.include_router(data.router)

# Phase 5~6에서 라우터를 여기에 마저 연결합니다.
# from routers import conversations, chat
# app.include_router(conversations.router)
# app.include_router(chat.router)
