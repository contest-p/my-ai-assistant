from firebase_admin import firestore

from config import db

DATA_COLLECTION = "data"
CONVERSATIONS_COLLECTION = "conversations"

# Firestore batch write 1건당 최대 500 operation 제한 (2.4)
BATCH_SIZE = 500


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
