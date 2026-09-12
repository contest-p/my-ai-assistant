"""KB_거래내역_비식별화.xlsx -> Firestore `data` 컬렉션 초기 적재 스크립트 (Task 2.2~2.5).

실행 (backend/ 디렉터리에서):
    python scripts/import_data.py               # 미리보기만 (Firestore에 쓰지 않음)
    python scripts/import_data.py --commit       # 실제 적재
    python scripts/import_data.py --commit --force   # data 컬렉션에 이미 문서가 있어도 강제 재적재
"""

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

import openpyxl  # noqa: E402

from services import firestore_service  # noqa: E402

DEFAULT_XLSX_PATH = BACKEND_ROOT / "data" / "KB_거래내역_비식별화.xlsx"

# PRD 7-1 / Task 2.3 매핑표. 여기 없는 적요는 항상 category=None (부호로 추측해서 채우지 않는다).
CATEGORY_MAP = {
    "체크카드": "카드결제",
    "국민카드": "카드결제",
    "카드입금": "카드결제",
    "오픈뱅킹출금": "계좌이체",
    "전자금융": "계좌이체",
    "CMS 공동": "계좌이체",
    "FBS출금": "계좌이체",
    "FBS 출금": "계좌이체",
    "FBS입금": "계좌이체",
    "뱅크페이": "계좌이체",
    "현금IC": "현금인출",
    "급여입금": "급여",
    "결산이자": "이자",
    "스마트입금": "기타입금",
    "센타입금": "기타입금",
}

EXPECTED_HEADER = ("거래일시", "적요", "보낸분/받는분", "송금메모", "출금액", "입금액", "잔액", "거래점", "구분")


def _find_header_row(rows: list[tuple]) -> int:
    for i, row in enumerate(rows):
        if row[: len(EXPECTED_HEADER)] == EXPECTED_HEADER:
            return i
    raise ValueError("엑셀에서 헤더 행(거래일시, 적요, ...)을 찾지 못했습니다.")


def _to_date(raw_datetime: str) -> str:
    # "2026.08.18 22:04:22" -> "2026-08-18" (시간 정보는 버린다, PRD 4-1)
    date_part = str(raw_datetime).split(" ")[0]
    return date_part.replace(".", "-")


def _build_memo(적요: str, counterparty, 출금액: float, 입금액: float) -> str:
    # 이미 비식별화된 엑셀이지만 "***", "토스 ***" 같은 마스킹 결과가 그대로 노출되지
    # 않도록, 마스킹된 값은 한 번 더 일반화된 문구로 치환한다 (PRD 3-3, Task 2.2).
    is_masked = counterparty is not None and "***" in str(counterparty)
    if is_masked:
        return "계좌이체 송금" if (출금액 or 0) > 0 else "계좌이체 입금"
    counterparty = (str(counterparty).strip() if counterparty else "") or None
    if counterparty:
        return f"{적요} · {counterparty}"
    return 적요


def load_records(xlsx_path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    rows = list(wb.active.iter_rows(values_only=True))
    header_idx = _find_header_row(rows)
    data_rows = rows[header_idx + 1 :]

    records = []
    for row in data_rows:
        거래일시 = row[0]
        if 거래일시 is None:
            # 합계 행 등 거래일시가 비어있는 행은 제외 (Task 2.2)
            continue
        적요, 보낸분_받는분, _송금메모, 출금액, 입금액 = row[1], row[2], row[3], row[4], row[5]
        출금액 = 출금액 or 0
        입금액 = 입금액 or 0

        records.append(
            {
                "date": _to_date(거래일시),
                "value": 입금액 - 출금액,
                "memo": _build_memo(적요, 보낸분_받는분, 출금액, 입금액),
                "category": CATEGORY_MAP.get(적요),
            }
        )
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX_PATH, help="입력 엑셀 경로")
    parser.add_argument("--commit", action="store_true", help="실제로 Firestore에 적재한다 (기본은 미리보기만)")
    parser.add_argument("--force", action="store_true", help="data 컬렉션에 이미 문서가 있어도 강제로 재적재한다")
    args = parser.parse_args()

    if not args.xlsx.exists():
        print(f"[오류] 엑셀 파일을 찾을 수 없습니다: {args.xlsx}")
        sys.exit(1)

    records = load_records(args.xlsx)

    total = len(records)
    income_count = sum(1 for r in records if r["value"] > 0)
    expense_count = sum(1 for r in records if r["value"] < 0)
    unmapped = sum(1 for r in records if r["category"] is None)

    print(f"파싱 결과: 총 {total}건 (입금 {income_count}건 / 지출 {expense_count}건 / 미분류 category {unmapped}건)")
    print("샘플 3건:")
    for r in records[:3]:
        print(" ", r)

    if total != 1116 or income_count != 254 or expense_count != 862:
        print("[경고] PRD 29번 기대값(총 1,116건 / 입금 254건 / 출금 862건)과 다릅니다. 적재 전에 원인을 확인하세요.")

    if not args.commit:
        print("\n--commit 옵션이 없어 미리보기만 했습니다. Firestore에는 아무것도 쓰지 않았습니다.")
        return

    if firestore_service.data_collection_has_documents() and not args.force:
        print("\n[중단] `data` 컬렉션에 이미 문서가 있습니다. 중복 적재를 방지하기 위해 중단합니다.")
        print("다시 적재하려면 --force 옵션을 명시적으로 붙여서 실행하세요.")
        sys.exit(1)

    added = firestore_service.batch_add_data(records)
    print(f"\nFirestore `data` 컬렉션에 {added}건 적재 완료.")


if __name__ == "__main__":
    main()
