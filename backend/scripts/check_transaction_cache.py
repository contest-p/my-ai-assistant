"""Offline smoke check: python scripts/check_transaction_cache.py (no pytest).

Inject config before application imports; never load credentials or contact services.
"""
import ast
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import socket
import sys
from threading import Event
from types import ModuleType
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def blocked(*args, **kwargs):
    raise AssertionError("Network access forbidden in offline verification")


original_connect = socket.socket.connect


def local_connect(sock, address):
    # Windows asyncio uses a loopback socket pair for its internal wakeup pipe.
    if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
        return original_connect(sock, address)
    return blocked()


socket.socket.connect = local_connect
socket.create_connection = blocked


class Snapshot:
    def __init__(self, key, record):
        self.id, self.record = key, deepcopy(record)
        self.exists = record is not None

    def to_dict(self):
        return deepcopy(self.record)


class Doc:
    def __init__(self, db, key):
        self.db, self.key = db, key

    def get(self):
        return Snapshot(self.key, self.db.rows.get(self.key))

    def set(self, record):
        self.db.rows[self.key] = {**record, "created_at": "2026-01-01"}

    def update(self, fields):
        self.db.rows[self.key].update(fields)

    def delete(self):
        del self.db.rows[self.key]


class FakeDB:
    def __init__(self):
        self.rows = {str(i): {"date": f"2026-{i % 8 + 1:02d}-01",
                    "value": 100 if i % 3 == 0 else -10, "memo": "synthetic",
                    "category": None if i % 2 else "custom", "created_at": "2026-01-01"}
                    for i in range(1116)}
        self.calls = self.reads = 0
        self.error = None
        self.entered = self.release = None

    def collection(self, name):
        assert name == "data", "Conversation access must be stubbed explicitly"
        return self

    def document(self, key=None):
        return Doc(self, key or "new")

    def stream(self, *, retry, timeout):
        assert retry is None and timeout == 15
        self.calls += 1
        snapshots = [Snapshot(k, v) for k, v in self.rows.items()]
        if self.entered:
            self.entered.set()
            assert self.release.wait(5)
        if self.error:
            # Partial streams must never become cached successful results.
            yield snapshots[0]
            raise self.error
        self.reads += len(snapshots)
        yield from snapshots


db = FakeDB()
config = ModuleType("config")
config.db = db
config.ALLOWED_ORIGINS = ["*"]
config.OPENAI_API_KEY = "offline-placeholder"
config.OPENAI_BASE_URL = "https://offline.invalid/v1"
config.OPENAI_MODEL = "gpt-5.5"
sys.modules["config"] = config

from google.api_core.exceptions import ResourceExhausted
from fastapi.testclient import TestClient
from services import firestore_service as fs, openai_service
from services.transaction_cache import TransactionCache, TransactionReadError
from main import app
from routers import chat

now = [0]
fs._transaction_cache = TransactionCache(clock=lambda: now[0])
client = TestClient(app)

with patch.object(openai_service, "ask", return_value="offline answer") as ai, \
     patch.object(fs, "add_conversation", return_value={"id": "conversation"}) as save:
    for i in range(20):
        assert client.get("/api/data/summary").json()["count"] == 1116
        assert client.get(f"/api/data?limit=20&offset={i * 20}").status_code == 200
        q = client.get(f"/api/data/quick-answer?kind=expenses&month=2026-01&offset={i * 20}")
        assert q.status_code == 200 and q.json()["expense"] == 930
        assert client.get("/api/data/export?format=json").status_code == 200
        assert ai.call_count == i
        assert client.post("/api/chat", json={"message": "합계"}).status_code == 200
    assert db.calls == 1 and db.reads == 1116 and save.call_count == 20
    print("PASS 100 mixed requests: 1 scan / 1116 document reads; quick lookup AI=0")

    rows = fs.fetch_all_data()
    rows[0]["category"] = "corrupt"
    rows.clear()
    assert fs.fetch_all_data()[0]["category"] == "custom"
    assert {r["category"] for r in fs.fetch_all_data()} == {None, "custom"}
    now[0] = 3600
    with ThreadPoolExecutor(max_workers=16) as pool:
        assert all(len(r) == 1116 for r in pool.map(lambda _: fs.fetch_all_data(), range(32)))
    assert db.calls == 2
    print("PASS TTL boundary, 32 concurrent requests / one fill, mutation isolation")

    payload = {"date": "2026-09-05", "value": 42, "memo": "new", "category": None}
    assert client.post("/api/data", json=payload).status_code == 201
    assert client.get("/api/data/summary").json()["current_month"]["month"] == "2026-09"
    assert client.put("/api/data/new", json={"category": "user-defined", "value": 43}).status_code == 200
    assert next(r for r in fs.fetch_all_data() if r["id"] == "new")["value"] == 43
    assert client.put("/api/data/new", json={"category": None}).status_code == 200
    assert next(r for r in fs.fetch_all_data() if r["id"] == "new")["category"] is None
    assert client.delete("/api/data/new").status_code == 200
    assert len(fs.fetch_all_data()) == 1116
    assert client.put("/api/data/missing", json={"value": 1}).status_code == 404
    assert client.delete("/api/data/missing").status_code == 404
    print("PASS CRUD invalidation, latest month, null/custom category, missing IDs")

    # Force a blocked load, then a write: old snapshot must be invalidated after write.
    db.entered, db.release = Event(), Event()
    with ThreadPoolExecutor(max_workers=2) as pool:
        read = pool.submit(fs.fetch_all_data)
        assert db.entered.wait(5)
        write = pool.submit(fs.update_data, "0", {"value": 999})
        db.release.set()
        read.result(timeout=5)
        write.result(timeout=5)
    db.entered = None
    assert next(r for r in fs.fetch_all_data() if r["id"] == "0")["value"] == 999
    print("PASS overlapping load/write: no old cache repopulation")

    # A write may commit even if reading back its response then fails.
    with patch.object(Doc, "get", side_effect=RuntimeError("post-write read failed")):
        try:
            fs.add_data(payload)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Expected readback failure")
    assert len(fs.fetch_all_data()) == 1117
    fs.delete_data("new")
    assert len(fs.fetch_all_data()) == 1116
    print("PASS committed write followed by response-read failure invalidates cache")

    for error in [ResourceExhausted("private details"), RuntimeError("private details")]:
        now[0] += 3600
        db.error = error
        before, ai_before = db.calls, ai.call_count
        with ThreadPoolExecutor(max_workers=12) as pool:
            def failed(_):
                try:
                    fs.fetch_all_data()
                except TransactionReadError:
                    return True
                return False
            assert all(pool.map(failed, range(24)))
        assert db.calls == before + 1
        for path in ["/api/data", "/api/data/summary", "/api/data/quick-answer", "/api/data/export"]:
            response = client.get(path)
            assert response.status_code == 503 and response.headers["retry-after"] == "60"
            assert "private" not in response.text
        assert client.post("/api/chat", json={"message": "합계"}).status_code == 503
        assert ai.call_count == ai_before
        db.error = None
        now[0] += 60
        assert len(fs.fetch_all_data()) == 1116 and db.calls == before + 2
    print("PASS partial-stream quota/DB errors, shared cooldown, 503, no stale fallback, recovery")

    with patch.object(fs, "get_conversation", return_value=None):
        assert client.post("/api/chat", json={"message": "x", "conversation_id": "missing"}).status_code == 404
    chat.SAVE_RETRY_DELAY_SECONDS = 0
    save.reset_mock()
    save.side_effect = [RuntimeError(), {"id": "saved"}]
    assert client.post("/api/chat", json={"message": "x"}).status_code == 200
    assert save.call_count == 2
    save.reset_mock()
    save.side_effect = RuntimeError()
    assert client.post("/api/chat", json={"message": "x"}).status_code == 500
    assert save.call_count == 2
    with patch.object(fs, "get_conversation", return_value={"messages": []}), \
         patch.object(fs, "append_messages") as append:
        assert client.post("/api/chat", json={"message": "x", "conversation_id": "existing"}).status_code == 200
        assert append.call_count == 1
    print("PASS chat save retry/success/500, continuation, missing conversation 404")

fs._transaction_cache = TransactionCache(clock=lambda: now[0])
db.error = ResourceExhausted("cold quota")
before = db.calls
assert client.get("/api/data").status_code == 503
assert client.get("/api/data").status_code == 503
assert db.calls == before + 1
db.error = None
now[0] += 60
assert len(fs.fetch_all_data()) == 1116
print("PASS cold-cache quota exhaustion and recovery")

db.rows.clear()
now[0] += 3600
before = db.calls
assert fs.fetch_all_data() == fs.fetch_all_data() == [] and db.calls == before + 1
assert client.get("/api/data/quick-answer").json()["count"] == 0
for source in Path(__file__).resolve().parents[1].rglob("*.py"):
    ast.parse(source.read_text(encoding="utf-8-sig"))
print("PASS valid empty cache and backend syntax; all checks offline")
