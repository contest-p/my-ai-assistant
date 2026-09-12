import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from models.schemas import ChatRequest
from services import analysis_service, firestore_service, openai_service

router = APIRouter(prefix="/api/chat", tags=["chat"])

SAVE_RETRY_DELAY_SECONDS = 0.5


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("")
def chat(payload: ChatRequest):
    is_new = payload.conversation_id is None
    existing_messages: list[dict] = []

    if not is_new:
        conversation = firestore_service.get_conversation(payload.conversation_id)
        if conversation is None:
            # 조용히 새 대화로 대체하지 않는다 (PRD 20번 예외 규칙, Task 6.4)
            raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
        existing_messages = conversation.get("messages", [])

    # 캐싱 금지 — 매 요청마다 analysis_service.get_summary()를 그대로 재사용한다 (Task 6.3-3)
    summary = analysis_service.get_summary()
    system_prompt = openai_service.build_system_prompt(summary)

    try:
        reply = openai_service.ask(system_prompt, existing_messages, payload.message)
    except Exception:
        # 원본 에러 메시지나 API 키를 노출하지 않는다 (PRD 25번)
        raise HTTPException(
            status_code=502, detail="AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해주세요."
        )

    user_message = {"role": "user", "content": payload.message, "timestamp": _now_iso()}
    assistant_message = {"role": "assistant", "content": reply, "timestamp": _now_iso()}

    def _save() -> str:
        if is_new:
            conversation = firestore_service.add_conversation(
                None, [user_message, assistant_message]
            )
            return conversation["id"]
        updated_messages = existing_messages + [user_message, assistant_message]
        firestore_service.append_messages(payload.conversation_id, updated_messages)
        return payload.conversation_id

    try:
        conversation_id = _save()
    except Exception:
        time.sleep(SAVE_RETRY_DELAY_SECONDS)
        try:
            conversation_id = _save()
        except Exception:
            # 저장 실패 시 AI 답변을 버리고 500 (Task 6.6 — 조용한 데이터 유실 방지)
            raise HTTPException(
                status_code=500, detail="답변을 저장하지 못했어요. 다시 시도해주세요."
            )

    return {
        "conversation_id": conversation_id,
        "reply": reply,
        "is_new_conversation": is_new,
    }
