from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
import mcp_server
from routers import chat, conversations, data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # mcp_server.mcp를 /mcp에 mount하면 mcp.streamable_http_app()이 자체적으로 갖고 있던
    # lifespan은 더 이상 실행되지 않는다 — host app(FastAPI)의 lifespan이 직접
    # mcp.session_manager.run()을 들어가 줘야 첫 /mcp 요청이 실패하지 않는다
    # (Task 10.3, py.sdk.modelcontextprotocol.io "Add to an existing app" 공식 문서 기준).
    async with mcp_server.mcp.session_manager.run():
        yield


app = FastAPI(title="전역 후 1년, 내 소비를 아는 AI 비서", lifespan=lifespan)

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

# Phase 10(보너스) — 새 Render 서비스 없이 같은 앱에 /mcp 경로로 MCP 서버를 노출한다 (Task 10.3).
app.mount("/mcp", mcp_server.build_mcp_asgi_app())
