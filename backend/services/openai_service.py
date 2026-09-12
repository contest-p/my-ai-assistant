from openai import OpenAI

import config

# 코디세이 프록시(sk-cody-live- 키)는 base_url을 넘기지 않으면 기본값인 api.openai.com으로
# 요청이 나가서 실패한다 (PRD 27, Task 6.1).
_client = OpenAI(api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)

MAX_TOKENS = 500

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
5. "이번 달 얼마 썼어? / 평소보다 많아?" 같은 질문에는 current_month와 trend를 함께 활용하세요.
6. "수입과 지출 차이가 얼마야? / 저축은 잘 하고 있어?" 같은 질문에는 net을 기준으로 답하세요.
7. "평균적으로 얼마씩 써?"에는 average_expense를, "평균적으로 얼마씩 받아?"에는 average_income을 쓰고 서로 혼동하지 마세요.
8. 월별 추세 질문에는 trend 정보를 활용하세요.
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


def ask(system_prompt: str, history: list[dict], user_message: str) -> str:
    """history: 기존 대화의 messages 배열(role/content만 사용). 신규 대화면 빈 리스트."""
    messages = [{"role": "system", "content": system_prompt}]
    for m in history:
        role = m.get("role")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": m.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    response = _client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content
