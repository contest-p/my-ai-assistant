"""선택 메뉴의 숫자 조회. AI 호출과 대화 저장 없이 서버에서 계산한다."""

from services.analysis_service import _months_between


def build_quick_answer(records: list[dict], kind: str, month: str, offset: int = 0) -> dict:
    dates = [r["date"] for r in records]
    months = _months_between(min(dates)[:7], max(dates)[:7]) if dates else []
    selected = [r for r in records if month == "all" or r["date"][:7] == month]
    incomes = [r for r in selected if r["value"] > 0]
    expenses = [r for r in selected if r["value"] < 0]
    income = sum(r["value"] for r in incomes)
    expense = sum(-r["value"] for r in expenses)
    items = []
    total = 0
    limit = 20
    if kind != "summary":
        candidates = incomes if kind == "income" else expenses
        if kind == "largest":
            candidates = sorted(candidates, key=lambda r: (r["value"], r["date"], r.get("id", "")))
            limit = 5
            offset = 0
        else:
            candidates = sorted(candidates, key=lambda r: (r["date"], r.get("id", "")), reverse=True)
        total = len(candidates)
        items = [{field: r.get(field) for field in ("id", "date", "value", "memo", "category")}
                 for r in candidates[offset:offset + limit]]
    return {
        "kind": kind, "month": month, "months": months,
        "period": f"{min(dates)} ~ {max(dates)}" if month == "all" and dates else None,
        "count": len(selected), "income_count": len(incomes), "expense_count": len(expenses),
        "income": income, "expense": expense, "net": income - expense,
        "items": items, "total": total, "offset": offset, "limit": limit,
        "has_more": kind in ("income", "expenses") and offset + limit < total,
    }
