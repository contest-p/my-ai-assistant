"""GET /api/data/summary 계산 로직 (PRD 13, Task 3.6).
이 파일의 get_summary()는 POST /api/chat(Phase 6)에서도 그대로 재사용한다 —
같은 계산 로직을 두 곳에 복붙하지 않는다.

calculate_trend()는 PRD 14 / Task 4.1~4.4 스펙 그대로다. get_summary()가 이 함수 없이는
동작할 수 없어 Phase 3 작업 중 함께 구현했다 — Phase 4에서는 이 로직에 대한 수동 검증
(4.5)만 남아있다.

"""

from datetime import datetime, timezone

from services.firestore_service import fetch_all_data


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


def build_insights(records: list[dict]) -> dict:
    monthly = []
    if records:
        dates = [r["date"] for r in records]
        buckets = {m: {"month": m, "income": 0, "expense": 0, "net": 0, "count": 0}
                   for m in _months_between(min(dates)[:7], max(dates)[:7])}
        for record in records:
            row = buckets[record["date"][:7]]
            value = record["value"]
            row["income"] += max(value, 0)
            row["expense"] += max(-value, 0)
            row["net"] += value
            row["count"] += 1
        monthly = list(buckets.values())
    income = sum(m["income"] for m in monthly)
    expense = sum(m["expense"] for m in monthly)
    peak = max(monthly, key=lambda m: m["expense"]) if expense else None
    return {
        "monthly": monthly,
        "insights": {
            "savings_rate": round((income - expense) / income * 100, 1) if income else None,
            "average_monthly_expense": expense / len(monthly) if monthly else 0,
            "peak_expense_month": {"month": peak["month"], "expense": peak["expense"]} if peak else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_summary() -> dict:
    """`data` 컬렉션 전체를 매번 다시 읽어서 계산한다 (페이지네이션된 목록 재사용 금지)."""
    return build_summary(fetch_all_data())


def build_summary(records: list[dict]) -> dict:
    """한 번 읽은 거래로 기본 요약과 인사이트를 함께 계산한다."""
    extended = build_insights(records)

    if not records:
        return {
            **extended,
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
        **extended,
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
