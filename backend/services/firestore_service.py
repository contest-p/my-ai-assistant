import time

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from config import db

DATA_COLLECTION = "data"
CONVERSATIONS_COLLECTION = "conversations"

# Firestore batch write 1건당 최대 500 operation 제한 (2.4)
BATCH_SIZE = 500

# 2026-09-13: summary 조회(GET /api/data/summary)와 채팅(POST /api/chat)이 매 요청마다
# fetch_all_data()로 `data` 컬렉션 전체를 캐싱 없이 재조회하다가 Firestore 무료 읽기
# 할당량(5만 read/일)을 소진해 "서버에 연결할 수 없어요" 장애가 발생했다(Render 로그
# 429 ResourceExhausted, Firebase 콘솔 읽기 100% 확인). TTL 캐싱으로 반복 조회를 흡수하되
# add/update/delete_data 시 즉시 무효화해 최신성을 지킨다. TTL 2분은 연속된 채팅
# 메시지·탭 전환처럼 짧은 시간 내 반복되는 재조회를 흡수하기에 충분하면서도, CUD 무효화가
# 실제 변경을 즉시 반영하므로 체감 최신성 저하는 크지 않다는 판단이다.
DATA_CACHE_TTL_SECONDS = 120
_data_cache: dict = {"records": None, "expires_at": 0.0}


def _invalidate_data_cache() -> None:
    _data_cache["records"] = None
    _data_cache["expires_at"] = 0.0


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
    _invalidate_data_cache()
    return added


def fetch_all_data() -> list[dict]:
    """`data` 컬렉션 전체를 읽는다 (summary 계산 전용, 3.6 주의사항 — 페이지네이션된
    목록을 재사용하지 않는다). TTL 캐싱으로 반복 조회 시 Firestore read를 절약하고,
    add/update/delete_data가 호출되면 즉시 무효화한다."""
    now = time.monotonic()
    if _data_cache["records"] is not None and now < _data_cache["expires_at"]:
        print(f"[cache] fetch_all_data HIT ({len(_data_cache['records'])}건, 만료까지 {_data_cache['expires_at'] - now:.0f}s)")
        return _data_cache["records"]
    records = [_doc_to_record(d) for d in db.collection(DATA_COLLECTION).stream()]
    _data_cache["records"] = records
    _data_cache["expires_at"] = now + DATA_CACHE_TTL_SECONDS
    print(f"[cache] fetch_all_data MISS - Firestore 재조회 ({len(records)}건)")
    return records


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
    _invalidate_data_cache()
    return _doc_to_record(doc_ref.get())


def update_data(doc_id: str, fields: dict) -> dict | None:
    """존재하지 않으면 None. 부분 수정만 반영(PUT이지만 PATCH처럼 동작, PRD 11번)."""
    doc_ref = db.collection(DATA_COLLECTION).document(doc_id)
    if not doc_ref.get().exists:
        return None
    if fields:
        doc_ref.update(fields)
    _invalidate_data_cache()
    return _doc_to_record(doc_ref.get())


def delete_data(doc_id: str) -> bool:
    doc_ref = db.collection(DATA_COLLECTION).document(doc_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    _invalidate_data_cache()
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
