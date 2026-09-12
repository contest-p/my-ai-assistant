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


TITLE_MAX_LENGTH = 30


def _auto_title(messages: list[dict]) -> str:
    # title이 비어있으면 첫 user 메시지로 자동 생성한다 (PRD 15-1, 30자 내외로 자름).
    # POST /api/conversations와 /api/chat(신규 대화)이 이 로직을 공유한다.
    first_user = next((m for m in messages if m.get("role") == "user"), None)
    if first_user is None:
        return "새 대화"
    content = (first_user.get("content") or "").strip()
    if not content:
        return "새 대화"
    if len(content) > TITLE_MAX_LENGTH:
        return content[:TITLE_MAX_LENGTH] + "..."
    return content


def add_conversation(title: str | None, messages: list[dict]) -> dict:
    title = title.strip() if title else ""
    if not title:
        title = _auto_title(messages)
    doc_ref = db.collection(CONVERSATIONS_COLLECTION).document()
    now = firestore.SERVER_TIMESTAMP
    doc_ref.set({"title": title, "messages": messages, "created_at": now, "updated_at": now})
    return _doc_to_record(doc_ref.get())


def append_messages(doc_id: str, messages: list[dict]) -> None:
    """messages: 기존 이력 + 새 메시지가 합쳐진 전체 배열. updated_at도 함께 갱신한다
    (5.3 "최신 대화가 목록 맨 위" 정렬이 실제로 동작하려면 필요, Task 6.6)."""
    db.collection(CONVERSATIONS_COLLECTION).document(doc_id).update(
        {"messages": messages, "updated_at": firestore.SERVER_TIMESTAMP}
    )


def list_conversations() -> list[dict]:
    """메타 정렬용으로 전체 문서를 읽는다 (updated_at DESC는 호출부에서 정렬)."""
    return [_doc_to_record(d) for d in db.collection(CONVERSATIONS_COLLECTION).stream()]


def get_conversation(doc_id: str) -> dict | None:
    snapshot = db.collection(CONVERSATIONS_COLLECTION).document(doc_id).get()
    return _doc_to_record(snapshot) if snapshot.exists else None


def delete_conversation(doc_id: str) -> bool:
    doc_ref = db.collection(CONVERSATIONS_COLLECTION).document(doc_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True
