from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from config import db

DATA_COLLECTION = "data"
CONVERSATIONS_COLLECTION = "conversations"

# Firestore batch write 1건당 최대 500 operation 제한 (2.4)
BATCH_SIZE = 500


def _doc_to_record(snapshot) -> dict:
    record = snapshot.to_dict()
    record["id"] = snapshot.id
    return record


def data_collection_has_documents() -> bool:
    """`data` 컬렉션에 문서가 1건이라도 있으면 True.
    초기 적재 스크립트의 중복 적재 방지 가드용 (2.4)."""
    docs = db.collection(DATA_COLLECTION).limit(1).get()
    return len(docs) > 0


def batch_add_data(records: list[dict]) -> int:
    """records: date/value/memo/category 키를 가진 dict 리스트.
    500건씩 나눠 batch commit하고, 적재된 문서 수를 반환한다."""
    added = 0
    for start in range(0, len(records), BATCH_SIZE):
        chunk = records[start : start + BATCH_SIZE]
        batch = db.batch()
        for record in chunk:
            doc_ref = db.collection(DATA_COLLECTION).document()
            batch.set(doc_ref, {**record, "created_at": firestore.SERVER_TIMESTAMP})
        batch.commit()
        added += len(chunk)
    return added


def fetch_all_data() -> list[dict]:
    """`data` 컬렉션 전체를 매번 다시 읽는다 (summary 계산 전용, 3.6 주의사항 —
    페이지네이션된 목록을 재사용하지 않는다)."""
    return [_doc_to_record(d) for d in db.collection(DATA_COLLECTION).stream()]


def query_data(start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """date 범위(양 끝 포함)로 필터링한 거래 목록. 정렬/페이지네이션은 호출부(router)에서 처리한다."""
    query = db.collection(DATA_COLLECTION)
    if start_date:
        query = query.where(filter=FieldFilter("date", ">=", start_date))
    if end_date:
        query = query.where(filter=FieldFilter("date", "<=", end_date))
    return [_doc_to_record(d) for d in query.stream()]


def add_data(record: dict) -> dict:
    doc_ref = db.collection(DATA_COLLECTION).document()
    doc_ref.set({**record, "created_at": firestore.SERVER_TIMESTAMP})
    return _doc_to_record(doc_ref.get())


def update_data(doc_id: str, fields: dict) -> dict | None:
    """존재하지 않으면 None. 부분 수정만 반영(PUT이지만 PATCH처럼 동작, PRD 11번)."""
    doc_ref = db.collection(DATA_COLLECTION).document(doc_id)
    if not doc_ref.get().exists:
        return None
    if fields:
        doc_ref.update(fields)
    return _doc_to_record(doc_ref.get())


def delete_data(doc_id: str) -> bool:
    doc_ref = db.collection(DATA_COLLECTION).document(doc_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True
