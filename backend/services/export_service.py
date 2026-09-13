"""선택 기간의 전체 거래를 내보낸다. 원본 파일은 변경하지 않는다."""

import csv
import io
import json

from services.analysis_service import _add_months
from services.firestore_service import fetch_all_data

FIELDS = ("id", "date", "value", "memo", "category")


def export_data(format: str, months: str) -> tuple[bytes, str]:
    records = fetch_all_data()
    if records and months != "all":
        latest = max(r["date"] for r in records)[:7]
        start = _add_months(latest, 1 - int(months)) + "-01"
        records = [r for r in records if r["date"] >= start]
    records = sorted(records, key=lambda r: (r["date"], r.get("id", "")), reverse=True)
    rows = [{field: r.get(field) for field in FIELDS} for r in records]
    if format == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8"), "application/json"
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(FIELDS)
    for row in rows:
        values = []
        for field in FIELDS:
            value = row[field]
            # Excel 등에서 텍스트를 수식으로 실행하지 않도록 보호한다. 숫자는 그대로 유지.
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                value = "'" + value
            values.append(value)
        writer.writerow(values)
    return output.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8"
