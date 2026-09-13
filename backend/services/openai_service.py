import json

from openai import OpenAI

import config
from services import analysis_service

# 코디세이 프록시(sk-cody-live- 키)는 base_url을 넘기지 않으면 기본값인 api.openai.com으로
# 요청이 나가서 실패한다 (PRD 27, Task 6.1).
_client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)

MAX_TOKENS = 500  # 1차 호출(도구 필요성 판단) 예산 — PRD 32번 그대로 유지.
# 도구 결과를 반영해 최종 답변을 만드는 2차 이후 호출 전용 예산. reasoning 모델(gpt-5.5)이
# "1년 소비 패턴 + 조언" 같은 종합형 질문에서 500 전부를 내부 reasoning에 써버려
# 빈 답변(finish_reason=length, content='')이 나오는 걸 실측으로 확인해서 늘렸다.
MAX_TOKENS_AFTER_TOOL = 1200
MAX_TOOL_ROUNDS = 3  # 방어적 상한 — 정상 흐름에서는 1라운드면 끝난다.
FALLBACK_REPLY = "지금은 이 질문에 제대로 답을 못 드리겠어요. 다시 한 번 질문해주시겠어요?"

# PRD 24-1 (2026-09-13 재설계: 카테고리·기간 통합 조회). analysis_service.get_transaction_summary()를
# 그대로 호출하는 tool 정의 — Phase 10의 MCP tool과 같은 계산 로직을 공유한다.
_CATEGORY_ENUM_LINES = "\n".join(
    f"  - {name}: {desc}" for name, desc in analysis_service.CATEGORY_DESCRIPTIONS.items()
)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_transaction_summary",
            "description": (
                "특정 기간 및/또는 카테고리로 거래를 집계해서 조회한다. "
                "start_date, end_date, category는 전부 선택값이다. "
                "이미 시스템 프롬프트에 전체 기간 요약(총 수입/지출/순증감/평균/이번 달/추세)이 "
                "들어있으므로, 세 값을 모두 생략해서 호출하지 않는다 — 그 경우는 이미 아는 정보와 "
                "완전히 같다. '이번 달'은 시스템 프롬프트의 이번 달 정보로 이미 답변 가능하니 이 "
                "도구를 쓰지 않는다. 그 외 임의 기간 질문('1달 전', '작년 11월' 등)이나 특정 "
                "카테고리 질문에만 사용한다.\n"
                "category enum 값과 의미(사용자 언어 → 이 값으로 매핑):\n" + _CATEGORY_ENUM_LINES
            ),
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": ["string", "null"],
                        "description": "조회 시작일 YYYY-MM-DD(포함). 생략하면 전체 기간 시작부터.",
                    },
                    "end_date": {
                        "type": ["string", "null"],
                        "description": "조회 종료일 YYYY-MM-DD(포함). 생략하면 최신 거래일까지.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "enum": analysis_service.CATEGORY_VALUES,
                        "description": "특정 카테고리만 조회할 때만 지정. 생략하면 카테고리별 지출 랭킹을 반환.",
                    },
                },
                "required": ["start_date", "end_date", "category"],
                "additionalProperties": False,
            },
        },
    }
]

# PRD 22번 시스템 프롬프트 템플릿 그대로. {current_month_label}은 PRD의
# `{current_month.month}` 표기를 실제 str.format() 키로 옮긴 것이다.
SYSTEM_PROMPT_TEMPLATE = """당신은 사용자의 개인 재정을 분석해주는 AI 비서입니다.

[사용자 데이터 요약]
- 데이터 기간: {period}
- 총 거래 건수: {count}건 (입금 {income_count}건 / 지출 {expense_count}건)
- 총 수입: {total_income}원 / 총 지출: {total_expense}원 / 순증감: {net}원
- 평균 입금액: {average_income}원 / 평균 지출액: {average_expense}원
- 최대 거래: {max_transaction}원 / 최소 거래: {min_transaction}원
- 이번 달({current_month_label}) 수입: {current_month_income}원 / 지출: {current_month_expense}원
- 최근 추세: {trend}

위 데이터를 기반으로 친근하고 구체적으로 답변하세요.

답변 규칙:
1. 가능한 경우 실제 데이터를 숫자로 인용하세요.
2. 데이터에 없는 사실은 임의로 추측하지 마세요.
3. 사용자의 질문과 관련된 데이터만 선택적으로 활용하세요.
4. "총 얼마 썼어?" 같은 질문에는 total_expense를 기준으로 답하세요.
5. "이번 달 얼마 썼어? / 평소보다 많아?" 같은 질문에는 current_month와 trend를 함께
   활용하세요. 단, "이번 달"은 오늘 실제 날짜가 아니라 데이터에 기록된 가장 최근
   거래월({current_month_label}) 기준입니다 — 답변에 실제 월을 자연스럽게 명시하세요
   (예: "이번 달(2026년 8월 기준)"). 실시간 최신 정보인 것처럼 월을 숨기고 말하지 마세요.
6. "수입과 지출 차이가 얼마야? / 저축은 잘 하고 있어?" 같은 질문에는 net을 기준으로 답하세요.
7. "평균적으로 얼마씩 써?"에는 average_expense를, "평균적으로 얼마씩 받아?"에는 average_income을 쓰고 서로 혼동하지 마세요.
8. 월별 추세 질문에는 trend 정보를 활용하세요.
9. "1년 동안 어땠어?", "앞으로 어떻게 하면 좋을까?" 같은 회고·조언성 질문에는, 연간
   총계와 추세(trend)에 근거해 구체적인 제안을 해도 됩니다 — 단, 데이터에 없는
   일반론("저축은 원래 소득의 20%가 좋아요" 같은 통념)을 근거 없이 던지지 말고,
   반드시 이 사용자의 실제 숫자를 근거로 삼으세요.
"""


def _won(amount) -> str:
    return f"{round(amount):,}"


def build_system_prompt(summary: dict) -> str:
    metrics = summary["metrics"]
    current_month = summary["current_month"]
    return SYSTEM_PROMPT_TEMPLATE.format(
        period=summary["period"],
        count=summary["count"],
        income_count=metrics["income_count"],
        expense_count=metrics["expense_count"],
        total_income=_won(metrics["total_income"]),
        total_expense=_won(metrics["total_expense"]),
        net=_won(metrics["net"]),
        average_income=_won(metrics["average_income"]),
        average_expense=_won(metrics["average_expense"]),
        max_transaction=_won(metrics["max_transaction"]),
        min_transaction=_won(metrics["min_transaction"]),
        current_month_label=current_month["month"],
        current_month_income=_won(current_month["income"]),
        current_month_expense=_won(current_month["expense"]),
        trend=summary["trend"],
    )


def _run_tool_call(tool_call) -> str:
    args = json.loads(tool_call.function.arguments)
    result = analysis_service.get_transaction_summary(
        start_date=args.get("start_date"),
        end_date=args.get("end_date"),
        category=args.get("category"),
    )
    return json.dumps(result, ensure_ascii=False)


def ask(system_prompt: str, history: list[dict], user_message: str) -> str:
    """history: 기존 대화의 messages 배열(role/content만 사용). 신규 대화면 빈 리스트."""
    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        role = m.get("role")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": m.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    for round_index in range(MAX_TOOL_ROUNDS):
        # 1차 호출(도구 필요성 판단)은 500 그대로, 도구 결과가 이미 반영된 2차 이후
        # 호출은 최종 답변용으로 더 넉넉한 예산을 준다.
        token_budget = MAX_TOKENS if round_index == 0 else MAX_TOKENS_AFTER_TOOL
        response = _client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            max_tokens=token_budget,
            tools=TOOLS,
        )
        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message.model_dump(exclude_none=True))
            for tool_call in message.tool_calls:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": _run_tool_call(tool_call),
                    }
                )
            continue

        if message.content:
            return message.content

        # tool_calls도 없고 content도 비어있음 — reasoning 모델이 이번 라운드 예산을
        # 답변을 한 글자도 못 내놓고 다 써버린 것(finish_reason=length 실측 확인).
        # "도구도 필요 없고 할 말도 없다"가 아니라 예산 부족이니, messages는 그대로 두고
        # 다음 라운드(더 큰 MAX_TOKENS_AFTER_TOOL)로 같은 요청을 재시도한다.

    # 방어적 상한(MAX_TOOL_ROUNDS)에 걸린 경우 — 정상 흐름에서는 도달하지 않는다.
    # 이미 도구 결과가 반영된 뒤라 최종 답변용 예산(MAX_TOKENS_AFTER_TOOL)을 그대로 쓴다.
    final = _client.chat.completions.create(
        model=config.OPENAI_MODEL, messages=messages, max_tokens=MAX_TOKENS_AFTER_TOOL
    )
    # 여기까지 왔는데도 빈 답변이면(재시도를 다 써도 reasoning이 예산을 계속 소진하는
    # 경우) 빈 문자열을 그대로 사용자에게 보여주지 않는다 — 고정 문구로 안전하게 떨어진다.
    return final.choices[0].message.content or FALLBACK_REPLY
