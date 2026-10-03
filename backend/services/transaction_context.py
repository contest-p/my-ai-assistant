"""같은 거래 스냅샷에서 채팅 근거를 만든다. DB 조회·AI 호출 없음."""

import json
from collections import defaultdict

# 1,116건은 보통 모두 포함된다. 증가 시 생략 건수를 명시한다.
DETAIL_MAX_ROWS = 2000
DETAIL_MAX_CHARACTERS = 160_000


def build_transaction_context(records: list[dict]) -> dict:
    expenses = sorted((r for r in records if r["value"] < 0),
                      key=lambda r: (r["value"], r["date"], r.get("id", "")))

    def detail(record):
        return [record["date"], record["value"], record.get("memo", ""), record.get("category")]

    categories = defaultdict(lambda: {"count": 0, "income": 0, "expense": 0})
    repeated = defaultdict(lambda: {"count": 0, "expense": 0, "months": set()})
    monthly_top = defaultdict(list)
    for record in records:
        category = record.get("category")
        row = categories[category]
        row["count"] += 1
        row["income"] += max(record["value"], 0)
        row["expense"] += max(-record["value"], 0)
        if record["value"] < 0:
            # memo·category 그대로 집계하며 추측으로 재분류하지 않는다.
            row = repeated[(record.get("memo", ""), category)]
            row["count"] += 1
            row["expense"] -= record["value"]
            row["months"].add(record["date"][:7])
    for record in expenses:
        month = record["date"][:7]
        if len(monthly_top[month]) < 5:
            monthly_top[month].append(detail(record))

    details = []
    characters = 0
    for record in sorted(records, key=lambda r: (r["date"], r.get("id", "")), reverse=True):
        row = detail(record)
        size = len(json.dumps(row, ensure_ascii=False))
        if len(details) >= DETAIL_MAX_ROWS or characters + size > DETAIL_MAX_CHARACTERS:
            break
        details.append(row)
        characters += size
    repeats = sorted((item for item in repeated.items() if item[1]["count"] >= 2),
                     key=lambda item: item[1]["expense"], reverse=True)
    return {
        "detail_columns": ["date", "value (입금+ / 출금-)", "memo", "category"],
        "detail_total_count": len(records),
        "detail_included_count": len(details),
        "detail_omitted_count": len(records) - len(details),
        "details": details,
        "top_expenses": [detail(r) for r in expenses[:10]],
        "top_10_expense_share_percent": (
            round(sum(-r["value"] for r in expenses[:10]) / sum(-r["value"] for r in expenses) * 100, 1)
            if expenses else None
        ),
        "monthly_top_expenses": dict(sorted(monthly_top.items())),
        "category_totals": [{"category": category, **totals} for category, totals in categories.items()],
        "repeated_memo_total_groups": len(repeats),
        "repeated_memo_omitted_groups": max(len(repeats) - 30, 0),
        "repeated_memos": [
            {"memo": memo, "category": category, "count": totals["count"],
             "expense": totals["expense"], "months": sorted(totals["months"])}
            for (memo, category), totals in repeats
        ][:30],
        "coverage": {
            "first_date": min((r["date"] for r in records), default=None),
            "last_date": max((r["date"] for r in records), default=None),
            "note": "기간 양끝 월은 일부 기간일 수 있음. 반복 거래만으로 고정비를 확정하지 않음.",
        },
    }
