"""Phase 10 (보너스) — MCP Server.

Python `mcp` SDK(streamable-http transport)를 기존 FastAPI 앱(main.py)에 마운트해서
같은 Render 서비스, 같은 도메인 아래 `/mcp` 경로로 노출한다(신규 배포 없음, Task 10.3).
공식 문서(py.sdk.modelcontextprotocol.io, `mcp` 2.2.0 기준) 확인 결과, 이 버전의 클래스명은
`FastMCP`가 아니라 `mcp.server.MCPServer`다 — 마운트 방식도 `streamable_http_app()`이
반환하는 Starlette 앱을 그대로 이어붙이는 형태로 바뀌었다.

`get_transaction_summary` tool(Task 10.4, PRD 24-1)은 services/analysis_service.py의
계산 로직을 그대로 호출한다 — Task 10.1의 Function Calling(services/openai_service.py)과
같은 함수를 공유하며, 계산 로직을 두 곳에 새로 만들지 않는다.
"""

from typing import Annotated, Literal
from urllib.parse import parse_qs

from mcp.server import MCPServer
from pydantic import Field
from starlette.responses import JSONResponse

import config
from services import analysis_service

Category = Literal["카드결제", "계좌이체", "현금인출", "급여", "이자", "기타입금"]

_CATEGORY_ENUM_LINES = "\n".join(
    f"- {name}: {desc}" for name, desc in analysis_service.CATEGORY_DESCRIPTIONS.items()
)

mcp = MCPServer(
    name="my-ai-assistant-finance",
    title="개인 소비 데이터 조회",
    instructions=(
        "사용자의 개인 소비/입출금 내역을 조회하는 도구를 제공한다. "
        "get_transaction_summary 하나만 있으며, 특정 기간·카테고리 질문에만 사용한다."
    ),
)


@mcp.tool(
    description=(
        "특정 기간 및/또는 카테고리로 거래를 집계해서 조회한다(PRD 24-1). "
        "start_date, end_date, category 모두 선택값이며, 셋 다 생략해서 호출하지 않는다 "
        "— 그건 전체 기간·전체 카테고리 요약이라 의미가 없는 호출이다. "
        "category를 생략하면 해당 기간의 카테고리별 지출 랭킹(breakdown)을 반환하고, "
        "지정하면 그 카테고리만 필터링한 금액/건수를 반환한다.\n"
        "category enum 값과 의미(사용자 언어 → 이 값으로 매핑):\n" + _CATEGORY_ENUM_LINES
    )
)
def get_transaction_summary(
    start_date: Annotated[
        str | None, Field(description="조회 시작일 YYYY-MM-DD(포함). 생략하면 전체 기간 시작부터.")
    ] = None,
    end_date: Annotated[
        str | None, Field(description="조회 종료일 YYYY-MM-DD(포함). 생략하면 최신 거래일까지.")
    ] = None,
    category: Annotated[
        Category | None, Field(description="특정 카테고리만 조회할 때만 지정.")
    ] = None,
) -> dict:
    return analysis_service.get_transaction_summary(
        start_date=start_date, end_date=end_date, category=category
    )


class SharedSecretAuthMiddleware:
    """Task 10.5 — 공유 비밀키 인증, URL 쿼리 파라미터(`?key=...`) 방식.

    처음엔 커스텀 헤더(X-MCP-Secret)로 구현했는데, Claude.ai의 헤더 인증
    (static_headers)은 조직(organization) 관리자용 beta 기능으로 보이고 무료/개인
    플랜의 커스텀 커넥터 설정 화면엔 아예 안 뜰 가능성이 높다는 지적을 반영해
    쿼리 파라미터 방식으로 바꿨다 — 커넥터 URL 입력창(`https://.../mcp?key=<비밀키>`)
    하나만 있으면 되므로 플랜에 상관없이 항상 되는 방법이다. 접근 로그에 비밀키가
    평문으로 남는 트레이드오프는 있지만, 이 프로젝트 규모(개인용, 조회 전용 API 1개)에서는
    감수할 만하다고 판단했다.

    Starlette Mount는 sub-app 앞에서 이 미들웨어를 거치게 하려면 미들웨어로 감싼
    ASGI app을 그대로 mount해야 한다(Mount(middleware=[...])는 route 자체에는
    적용되지만 우리는 이미 만들어진 app 객체를 감싸는 쪽이 더 단순하다).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        secret = config.MCP_SHARED_SECRET
        query = parse_qs(scope.get("query_string", b"").decode("utf-8", "replace"))
        provided = query.get("key", [None])[0]

        if not secret or provided != secret:
            response = JSONResponse({"detail": "Unauthorized"}, status_code=401)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def build_mcp_asgi_app():
    """main.py에서 app.mount("/mcp", ...)로 그대로 넘길 ASGI app."""
    inner = mcp.streamable_http_app(
        streamable_http_path="/",
        transport_security=config.mcp_transport_security(),
    )
    return SharedSecretAuthMiddleware(inner)
