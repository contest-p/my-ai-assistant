from firebase_admin import firestore
from google.api_core.exceptions import ResourceExhausted

from services.transaction_cache import TransactionCache

from config import db

DATA_COLLECTION = "data"
CONVERSATIONS_COLLECTION = "conversations"

# Firestore batch write 1건당 최대 500 operation 제한 (2.4)
BATCH_SIZE = 500

_transaction_cache = TransactionCache()

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
    """500건씩 batch commit한다. 별도 프로세스의 캐시는 무효화하지 못한다."""
    with _transaction_cache.mutation():
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
    """All transaction consumers share a one-hour process-local snapshot."""
    def load():
        # Disable SDK retries, including stream retries, on quota/DB failure.
        return [_doc_to_record(d) for d in
                db.collection(DATA_COLLECTION).stream(retry=None, timeout=15)]

    return _transaction_cache.get(load, lambda exc: isinstance(exc, ResourceExhausted))


def query_data(start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """Inclusive range filtering over the shared full snapshot."""
    return [r for r in fetch_all_data()
            if (not start_date or r["date"] >= start_date)
            and (not end_date or r["date"] <= end_date)]


def add_data(record: dict) -> dict:
    with _transaction_cache.mutation():
        doc_ref = db.collection(DATA_COLLECTION).document()
        doc_ref.set({**record, "created_at": firestore.SERVER_TIMESTAMP})
        return _doc_to_record(doc_ref.get())


def update_data(doc_id: str, fields: dict) -> dict | None:
    """존재하지 않으면 None. 부분 수정만 반영한다."""
    with _transaction_cache.mutation():
        doc_ref = db.collection(DATA_COLLECTION).document(doc_id)
        if not doc_ref.get().exists:
            return None
        if fields:
            doc_ref.update(fields)
        return _doc_to_record(doc_ref.get())


def delete_data(doc_id: str) -> bool:
    with _transaction_cache.mutation():
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


CONVERSATIONS_LIST_LIMIT = 20


def list_conversations() -> tuple[list[dict], bool]:
    """최근 대화 최대 CONVERSATIONS_LIST_LIMIT건과 '더 있음(has_more)' 여부를 함께
    반환한다 (updated_at DESC, 호출부 정렬은 그대로 둬 응답 형식을 바꾸지 않는다).
    2026-09-13: 대화 수가 늘어날수록 매 요청 전체 스캔이 Firestore 할당량을 위협해
    상한을 두었다. has_more 판별을 위해 상한보다 1건 더 조회(추가 read 1건)하고
    초과분은 잘라낸다."""
    query = (
        db.collection(CONVERSATIONS_COLLECTION)
        .order_by("updated_at", direction=firestore.Query.DESCENDING)
        .limit(CONVERSATIONS_LIST_LIMIT + 1)
    )
    records = [_doc_to_record(d) for d in query.stream()]
    has_more = len(records) > CONVERSATIONS_LIST_LIMIT
    return records[:CONVERSATIONS_LIST_LIMIT], has_more


def get_conversation(doc_id: str) -> dict | None:
    snapshot = db.collection(CONVERSATIONS_COLLECTION).document(doc_id).get()
    return _doc_to_record(snapshot) if snapshot.exists else None


def delete_conversation(doc_id: str) -> bool:
    doc_ref = db.collection(CONVERSATIONS_COLLECTION).document(doc_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True
