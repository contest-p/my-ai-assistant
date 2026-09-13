"""GET /api/data/summary 계산 로직 (PRD 13, Task 3.6).
이 파일의 get_summary()는 POST /api/chat(Phase 6)에서도 그대로 재사용한다 —
같은 계산 로직을 두 곳에 복붙하지 않는다.

calculate_trend()는 PRD 14 / Task 4.1~4.4 스펙 그대로다. get_summary()가 이 함수 없이는
동작할 수 없어 Phase 3 작업 중 함께 구현했다 — Phase 4에서는 이 로직에 대한 수동 검증
(4.5)만 남아있다.

get_transaction_summary()는 PRD 24-1(2026-09-13 재설계: 카테고리·기간 통합 조회) 스펙이다.
Task 10.1의 /api/chat Function Calling과 Task 10.4의 MCP tool이 이 함수를 그대로 같이
호출한다 — 두 채널이 같은 계산 로직을 따로 구현하지 않는다.
"""

from services.firestore_service import fetch_all_data

# PRD 7-1 매핑표(scripts/import_data.py의 CATEGORY_MAP)가 실제로 만들어내는 category 값.
# PRD 24-1의 enum 및 각 값 설명과 동일하다 — Function Calling(10.1)과 MCP tool(10.4)
# 스키마가 이 딕셔너리 하나를 같이 참조해서 설명 문구가 따로 어긋나지 않게 한다.
CATEGORY_DESCRIPTIONS = {
    "카드결제": "체크카드·신용카드·국민카드로 결제한 거래",
    "계좌이체": "오픈뱅킹·전자금융 등 계좌 간 이체",
    "현금인출": "ATM 등 현금 출금",
    "급여": "급여 입금",
    "이자": "결산이자 입금",
    "기타입금": "위에 해당하지 않는 입금",
}
CATEGORY_VALUES = list(CATEGORY_DESCRIPTIONS.keys())


def _month_key(date_str: str) -> str:
    return date_str[:7]  # "YYYY-MM-DD" -> "YYYY-MM"


def _add_months(year_month: str, delta: int) -> str:
    year, month = map(int, year_month.split("-"))
    idx = year * 12 + (month - 1) + delta
    year2, month2 = divmod(idx, 12)
    return f"{year2:04d}-{month2 + 1:02d}"


def _months_between(start_ym: str, end_ym: str) -> list[str]:
    months = []
    cur = start_ym
    while cur <= end_ym:
        months.append(cur)
        cur = _add_months(cur, 1)
    return months


def calculate_trend(records: list[dict]) -> str:
    """월별 총 지출액 기준으로 최근 3개월과 이전 3개월 평균을 비교한다 (PRD 14)."""
    if not records:
        return "비교할 수 있는 충분한 월별 데이터가 없습니다."

    monthly_expense: dict[str, float] = {}
    for r in records:
        if r["value"] < 0:
            ym = _month_key(r["date"])
            monthly_expense[ym] = monthly_expense.get(ym, 0) + abs(r["value"])

    dates = [r["date"] for r in records]
    min_ym, max_ym = _month_key(min(dates)), _month_key(max(dates))
    all_months = _months_between(min_ym, max_ym)  # 거래 없는 월도 0원으로 채운다 (14-1)

    if len(all_months) < 6:
        return "비교할 수 있는 충분한 월별 데이터가 없습니다."

    recent_months = [_add_months(max_ym, -i) for i in (2, 1, 0)]
    previous_months = [_add_months(max_ym, -i) for i in (5, 4, 3)]

    recent_avg = sum(monthly_expense.get(m, 0) for m in recent_months) / 3
    previous_avg = sum(monthly_expense.get(m, 0) for m in previous_months) / 3

    if previous_avg == 0:
        return "이전 3개월 지출이 0원이라 변화율을 계산할 수 없습니다."

    change_rate = (recent_avg - previous_avg) / previous_avg * 100

    if -5 <= change_rate <= 5:
        return "최근 3개월 지출이 비슷한 수준으로 유지되고 있어요."

    direction = "증가" if change_rate > 5 else "감소"
    sign = "+" if change_rate > 0 else "-"
    return f"최근 3개월 월평균 지출 {direction} ({sign}{abs(round(change_rate))}%)"


def get_summary() -> dict:
    """`data` 컬렉션 전체를 매번 다시 읽어서 계산한다 (페이지네이션된 목록 재사용 금지)."""
    records = fetch_all_data()

    if not records:
        return {
            "period": None,
            "count": 0,
            "metrics": {
                "total_income": 0,
                "total_expense": 0,
                "net": 0,
                "income_count": 0,
                "expense_count": 0,
                "average_income": 0,
                "average_expense": 0,
                "max_transaction": 0,
                "min_transaction": 0,
            },
            "current_month": {"month": None, "income": 0, "expense": 0, "net": 0},
            "trend": calculate_trend(records),
        }

    values = [r["value"] for r in records]
    incomes = [v for v in values if v > 0]
    expenses = [v for v in values if v < 0]

    total_income = sum(incomes)
    total_expense = sum(abs(v) for v in expenses)
    income_count = len(incomes)
    expense_count = len(expenses)

    dates = [r["date"] for r in records]
    period = f"{min(dates)} ~ {max(dates)}"

    latest_month = _month_key(max(dates))
    month_values = [r["value"] for r in records if _month_key(r["date"]) == latest_month]
    month_income = sum(v for v in month_values if v > 0)
    month_expense = sum(abs(v) for v in month_values if v < 0)

    return {
        "period": period,
        "count": len(records),
        "metrics": {
            "total_income": total_income,
            "total_expense": total_expense,
            "net": total_income - total_expense,
            "income_count": income_count,
            "expense_count": expense_count,
            "average_income": total_income / income_count if income_count else 0,
            "average_expense": total_expense / expense_count if expense_count else 0,
            "max_transaction": max(values),
            "min_transaction": min(values),
        },
        "current_month": {
            "month": latest_month,
            "income": month_income,
            "expense": month_expense,
            "net": month_income - month_expense,
        },
        "trend": calculate_trend(records),
    }


def get_transaction_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
) -> dict:
    """PRD 24-1. 세 파라미터 모두 선택값이다.

    - category 생략: 기간(생략 시 전체 기간) 내 수입/지출/순증감/건수 + 카테고리별
      지출 랭킹(breakdown, 지출액 내림차순).
    - category 지정: 그 카테고리로 필터링한 지출액/건수만 반환.

    get_summary()와 마찬가지로 `data` 컬렉션 전체를 fetch_all_data()로 다시 읽어
    메모리에서 필터링한다(페이지네이션된 목록 재사용 금지, 3.6과 동일 원칙).
    """
    records = fetch_all_data()
    if start_date:
        records = [r for r in records if r["date"] >= start_date]
    if end_date:
        records = [r for r in records if r["date"] <= end_date]

    result: dict = {}
    if start_date:
        result["start_date"] = start_date
    if end_date:
        result["end_date"] = end_date

    if category:
        matched = [r for r in records if r.get("category") == category]
        result["category"] = category
        result["expense"] = sum(abs(r["value"]) for r in matched)
        result["count"] = len(matched)
        return result

    incomes = [r["value"] for r in records if r["value"] > 0]
    expenses = [r["value"] for r in records if r["value"] < 0]
    income = sum(incomes)
    expense = sum(abs(v) for v in expenses)

    by_category: dict[str, dict] = {}
    for r in records:
        cat = r.get("category")
        if cat is None:
            continue
        entry = by_category.setdefault(cat, {"category": cat, "expense": 0, "count": 0})
        entry["expense"] += abs(r["value"])
        entry["count"] += 1
    breakdown = sorted(by_category.values(), key=lambda e: e["expense"], reverse=True)

    result.update(
        {
            "income": income,
            "expense": expense,
            "net": income - expense,
            "count": len(records),
            "breakdown": breakdown,
        }
    )
    return result
