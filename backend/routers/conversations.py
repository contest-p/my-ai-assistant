from fastapi import APIRouter, HTTPException

from models.schemas import ConversationCreate
from services import firestore_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", status_code=201)
def create_conversation(payload: ConversationCreate):
    # ⚠ 이 엔드포인트는 /api/chat의 자동저장(Phase 6)과 별개다. 여긴 미션이 요구하는
    # 독립 API이자 수동 백업/가져오기용이며, 일반 채팅 흐름에서는 호출되지 않는다
    # (PRD 15번 중복 저장 방지 규칙 — Phase 8 프론트 연동 시 반드시 지킬 것).
    messages = [m.model_dump() for m in payload.messages]
    conversation = firestore_service.add_conversation(payload.title, messages)
    return {
        "id": conversation["id"],
        "title": conversation["title"],
        "created_at": conversation["created_at"],
        "message_count": len(conversation["messages"]),
    }


@router.get("")
def list_conversations():
    conversations, has_more = firestore_service.list_conversations()
    conversations.sort(key=lambda c: c.get("updated_at"), reverse=True)
    items = [
        {
            "id": c["id"],
            "title": c["title"],
            "created_at": c["created_at"],
            "updated_at": c["updated_at"],
            "message_count": len(c.get("messages", [])),
        }
        for c in conversations
    ]
    # count: 전체 대화 수가 아니라 "이번 응답에 실제로 포함된 항목 수"다. 2026-09-13
    # list_conversations()에 상한(20)이 생기면서 전체 수와 달라질 수 있어 has_more로 보완한다.
    return {"count": len(items), "items": items, "has_more": has_more}


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str):
    conversation = firestore_service.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    return {
        "id": conversation["id"],
        "title": conversation["title"],
        "created_at": conversation["created_at"],
        "updated_at": conversation["updated_at"],
        "messages": conversation.get("messages", []),
    }


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str):
    deleted = firestore_service.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    return {"deleted": True, "id": conversation_id}
