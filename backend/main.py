from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from services.transaction_cache import TransactionReadError

import config
from routers import chat, conversations, data


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
app.include_router(conversations.router)
app.include_router(chat.router)


@app.exception_handler(TransactionReadError)
async def transaction_read_error(request, exc):
    detail = (
        "거래 데이터 조회 한도를 초과했어요. 한도가 회복된 뒤 다시 시도해주세요. 반복 새로고침은 도움이 되지 않아요."
        if exc.quota else
        "거래 데이터를 불러오지 못했어요. 잠시 후 다시 시도해주세요."
    )
    return JSONResponse(status_code=503, content={"detail": detail},
                        headers={"Retry-After": str(exc.retry_after)})
