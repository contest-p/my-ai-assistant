# Task.md — 개발 작업 분해

> 기준 문서: `PRD.md`, `기술스택.md`
> 총 Phase 10개(핵심 기능 1~9 + 보너스 10)
> 이 문서의 상단 체크리스트는 **진행 상황 공유용**입니다. 각 항목을 "Phase.Task 번호"로
> 하단 "상세 스펙"과 연결했으니, 다음 세션에서는 번호만 보고 해당 섹션으로 바로 가면 됩니다.
> 작업 순서는 위에서 아래로 진행하는 걸 기본으로 하되, Phase 1~2는 한 번만 하면 되는
> 세팅성 작업이라 이후 Phase와 병행해도 무방합니다.

---

## 전체 체크리스트

### Phase 1. 프로젝트 초기 설정
- [ ] 1.1 GitHub 저장소 생성 (단일 repo, `backend/` + `frontend/`)
- [ ] 1.2 backend 폴더 뼈대 생성 (routers/services/models 분리)
- [ ] 1.3 Python 3.11 가상환경 구성 + 패키지 설치
- [ ] 1.4 Firebase 프로젝트 생성 + Firestore 활성화 + 서비스 계정 키 발급
- [ ] 1.5 OpenAI API 키 발급
- [ ] 1.6 FastAPI 앱 초기화 (CORS `*`, 헬스체크)
- [ ] 1.7 로컬 실행 + Swagger(`/docs`) 확인

### Phase 2. Firestore 연동 + 초기 데이터 적재
- [ ] 2.1 firebase-admin 초기화 (`config.py`)
- [ ] 2.2 `KB_거래내역_비식별화.xlsx` → (date, value, memo, category) 변환 스크립트
- [ ] 2.3 category 매핑 로직 구현
- [ ] 2.4 Firestore `data` 컬렉션 bulk upload
- [ ] 2.5 적재 검증 (1,116건, 입금+출금=1,116건)

### Phase 3. 데이터 API (CRUD + Summary)
- [ ] 3.1 Pydantic 모델 정의 (`schemas.py`)
- [ ] 3.2 `POST /api/data`
- [ ] 3.3 `GET /api/data` (페이지네이션, inclusive 날짜 필터, 정렬)
- [ ] 3.4 `PUT /api/data/{id}`
- [ ] 3.5 `DELETE /api/data/{id}`
- [ ] 3.6 `GET /api/data/summary` (수입/지출/평균/최대/최소/이번달)
- [ ] 3.7 Swagger에서 5개 엔드포인트 수동 테스트

### Phase 4. Trend 계산 로직
- [ ] 4.1 월별 지출 집계 함수 (거래 없는 월 = 0원)
- [ ] 4.2 최근 3개월 vs 이전 3개월 비교 구간 확정 (데이터 최신월 기준)
- [ ] 4.3 변화율 계산
- [ ] 4.4 판정 기준(±5%)
- [ ] 4.5 예외 처리 (데이터 부족 / 이전 기간 0원) + summary 연결·수동 검증

### Phase 5. 대화 기록 API
- [ ] 5.1 Pydantic 모델 정의 (Conversation, Message)
- [ ] 5.2 `POST /api/conversations`
- [ ] 5.3 `GET /api/conversations` (메타만)
- [ ] 5.4 `GET /api/conversations/{id}` (전체 메시지)
- [ ] 5.5 `DELETE /api/conversations/{id}`
- [ ] 5.6 Swagger에서 저장→목록→불러오기→삭제 흐름 테스트

### Phase 6. AI 챗봇 API
- [ ] 6.1 OpenAI 클라이언트 초기화 (`OPENAI_BASE_URL`, `OPENAI_MODEL` 환경변수)
- [ ] 6.2 시스템 프롬프트 조립 함수
- [ ] 6.3 `POST /api/chat` — 신규/기존 대화 분기
- [ ] 6.4 존재하지 않는 `conversation_id` 404 처리
- [ ] 6.5 GPT 호출 + `max_tokens` 제한
- [ ] 6.6 대화 자동 저장 로직
- [ ] 6.7 실제 질문으로 통합 테스트 (기본 질문 4개, PRD 23번)

### Phase 7. 백엔드 배포 (Render)
- [ ] 7.1 `requirements.txt` 확정 (`pip freeze`)
- [ ] 7.2 GitHub push
- [ ] 7.3 Render Web Service 생성 (Root Directory=`backend`)
- [ ] 7.4 환경변수 5종 등록
- [ ] 7.5 배포 URL `/docs` 확인 + 콜드스타트 체감

### Phase 8. 프론트엔드 개발
- [ ] 8.1 `mockup/` → `frontend/`로 이관 + `config.js` 추가
- [ ] 8.2 `api.js` (fetch 래퍼)
- [ ] 8.3 채팅 화면 실연동 (로딩/오류/새 대화)
- [ ] 8.4 데이터 관리 화면 실연동 (목록/추가/수정/삭제)
- [ ] 8.5 대화 기록 화면 실연동 (목록/불러오기)
- [ ] 8.6 데이터 요약 화면 실연동
- [ ] 8.7 콜드스타트 안내 문구 연결
- [ ] 8.8 로컬에서 백엔드(localhost) 연동 테스트, CORS 확인

### Phase 9. 프론트엔드 배포 + 통합 검증
- [ ] 9.1 GitHub push
- [ ] 9.2 Vercel 배포 (Root Directory=`frontend`, Other preset)
- [ ] 9.3 `frontend/js/config.js`의 `API_BASE_URL`을 Render 배포 URL로 변경 후 커밋·재배포
- [ ] 9.4 Render `ALLOWED_ORIGINS`를 Vercel 도메인으로 좁히기
- [ ] 9.5 PRD 37번 검증 기준 전체 재확인 (배포 URL 기준)
- [ ] 9.6 README.md 작성 + 스크린샷 3종 촬영

### Phase 10. 보너스 — Function Calling + MCP Server 연동
- [x] 10.1 `POST /api/chat`에 실제 OpenAI Function Calling 추가 (`get_transaction_summary`
      1개, tools 파라미터·tool_call 응답 처리·재호출)
- [ ] 10.2 실제 도구 호출 통합 테스트 (PRD 24-3 흐름, "작년 11월엔 뭘 제일 많이 썼어?" 등) —
      로컬에서 tool_calls 발생까지는 로그로 확인, Firestore 쓰기 쿼터 소진으로 저장 단계
      500까지 봤음(코드 문제 아님). 쿼터 회복 후 마지막 저장까지 재확인 필요.
- [x] 10.3 MCP 서버를 기존 FastAPI 앱에 마운트 (신규 배포 없음)
- [x] 10.4 `get_transaction_summary`를 MCP tool로 노출 (10.1의 서비스 함수 재사용)
- [x] 10.5 최소 인증 — 공유 비밀키(URL 쿼리 파라미터 `?key=` 방식, 헤더에서 변경)
- [ ] 10.6 환경변수 추가 등록 + 재배포 — 코드/로컬 검증 완료, Render 대시보드 등록·재배포는
      사용자가 직접 진행
- [ ] 10.7 Claude.ai 커스텀 커넥터로 연결, 실제 호출 흐름 검증
- [ ] 10.8 README에 연동 방법 + 호출 흐름 정리

---

## 상세 스펙

### Phase 1. 프로젝트 초기 설정

**1.1 GitHub 저장소 생성**
저장소 1개, 루트에 `backend/`, `frontend/` 두 폴더. (기술스택.md "단일 레포" 결정 반영)
`.gitignore` 루트에 하나: `.env`, `venv/`, `__pycache__/`, `*.xlsx`, `node_modules/`(해당 없으면 생략).

**1.2 backend 폴더 뼈대**
```
backend/
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── routers/        (data.py, conversations.py, chat.py — 아직 빈 파일)
├── services/        (firestore_service.py, openai_service.py, analysis_service.py)
├── models/          (schemas.py)
└── scripts/         (import_data.py)
```

**1.3 Python 3.11 가상환경**
`python3.11 -m venv venv` → 활성화 → `pip install fastapi uvicorn firebase-admin openai python-dotenv openpyxl`.
`openpyxl`이 빠지면 Phase 2.2에서 `KB_거래내역_비식별화.xlsx`를 못 읽으니 지금 같이 설치.

**1.4 Firebase 프로젝트**
Firebase Console에서 프로젝트 생성 → Firestore Database 활성화(프로덕션 모드) → 프로젝트 설정 >
서비스 계정 > 새 비공개 키 생성(JSON 다운로드). 이 JSON은 `backend/`에 커밋하지 않는다
(PRD 27, 28번).

**1.5 OpenAI API 키**
platform.openai.com에서 발급, 결제 정보 등록.

**1.6 FastAPI 앱 초기화**
`main.py`: FastAPI 인스턴스 생성, `CORSMiddleware`로 `allow_origins=["*"]`(개발 중), `GET /`
헬스체크(`{"status": "ok"}` 반환).

**1.7 로컬 실행 확인**
`uvicorn main:app --reload` → `http://localhost:8000/docs` 접속해서 Swagger UI 뜨는지 확인.
완료 기준: 헬스체크 200 응답, Swagger UI 정상 렌더링.

---

### Phase 2. Firestore 연동 + 초기 데이터 적재

**2.1 firebase-admin 초기화**
`config.py`에서 `FIREBASE_SERVICE_ACCOUNT_JSON` 환경변수(JSON 문자열)를 읽어
`credentials.Certificate(json.loads(...))`로 초기화. `firestore.client()`를 다른 모듈에서
가져다 쓸 수 있게 export.

**2.2 변환 스크립트**
`scripts/import_data.py`. 입력: `KB_거래내역_비식별화.xlsx`(프로젝트 루트 또는 별도 위치 —
저장소에는 커밋하지 않으므로 `.gitignore`에 포함, 로컬에서만 실행).
- `거래일시` → `date` (YYYY-MM-DD로 자름, 시간 정보는 버림 — PRD 4-1)
- `입금액 - 출금액` → `value` (부호 있는 정수 — PRD 4-1)
- `적요` + `보낸분/받는분` → `memo` (PRD 3-3 원칙: 개인 실명 노출 금지. 이미 비식별화된
  엑셀이므로 `***`, `토스 ***` 같은 마스킹 결과가 그대로 memo에 들어가지 않도록,
  이 값들이 나오면 일반화된 문구로 한 번 더 치환할 것 — 예: "계좌이체 송금")
- 합계 행(거래일시가 비어있는 마지막 행) 제외

**2.3 category 매핑**
PRD 7-1 매핑표를 그대로 딕셔너리로 구현:
```python
CATEGORY_MAP = {
    "체크카드": "카드결제", "국민카드": "카드결제", "카드입금": "카드결제",
    "오픈뱅킹출금": "계좌이체", "전자금융": "계좌이체", "CMS 공동": "계좌이체",
    "FBS출금": "계좌이체", "FBS 출금": "계좌이체", "FBS입금": "계좌이체", "뱅크페이": "계좌이체",
    "현금IC": "현금인출",
    "급여입금": "급여",
    "결산이자": "이자",
    "스마트입금": "기타입금", "센타입금": "기타입금",
}
```
**매핑에 없는 적요 값은 항상 `None`(→ Firestore null → JSON null)으로 저장한다.**
value 부호로 "기타입금/카드결제"를 임의로 추측해서 채우지 않는다 — 실제로 확인 안 된
분류를 만들어내는 것보다, 모른다는 걸 null로 정직하게 남기는 게 맞다. (참고: 실제
비식별화 파일의 적요 15종은 위 표로 전부 커버되므로, 이 분기는 현재 데이터에서는
사실상 발동하지 않는다 — 나중에 CRUD로 새 유형이 들어올 때를 위한 안전장치다.)

**2.4 bulk upload**
`firestore_service.py`에 `batch_add_data(records: list[dict])` 구현, Firestore의
`batch()`로 500건씩 나눠 커밋(Firestore batch write 한도가 500). `data` 컬렉션에 적재,
문서 ID는 auto-generate, 각 문서에 `created_at` 서버 타임스탬프 포함.
재실행 방지: 스크립트 시작 시 `data` 컬렉션에 문서가 1건이라도 있으면 경고를 출력하고
중단한다(중복 적재 방지). 다시 적재하려면 `--force` 같은 명시적 플래그를 요구한다 —
복잡한 락(lock) 구조까지는 필요 없고, "이미 있으면 멈추고 사람이 판단하게" 정도면 충분하다.

**2.5 적재 검증**
`import_data.py` 실행 결과 또는 Firestore Console을 사용해서 검증한다 — 이 시점엔
아직 `GET /api/data`가 없으니(Phase 3에서 구현) API로 확인하지 않는다.
완료 기준: 전체 거래 1,116건, `value > 0` 254건, `value < 0` 862건, 254 + 862 = 1,116건
(PRD 29번 초기 검증 기준). Phase 3 API 구현 완료 후 필요하면 API로 다시 확인할 수 있다.

---

### Phase 3. 데이터 API (CRUD + Summary)

**3.1 Pydantic 모델** (`models/schemas.py`)
```python
class DataCreate(BaseModel):
    date: str   # YYYY-MM-DD, PRD 25 검증
    value: float
    memo: str   # 빈 문자열 불허 (PRD 25)
    category: str | None = None

class DataUpdate(BaseModel):
    date: str | None = None
    value: float | None = None
    memo: str | None = None
    category: str | None = None
```
`date`는 정규식 `^\d{4}-\d{2}-\d{2}$`로 검증, 형식 위반 시 자동으로 422 (FastAPI 기본 동작).

**3.2 `POST /api/data`**
PRD 9-1 참고. 201 응답, 생성된 문서 전체 반환(`id`, `created_at` 포함).

**3.3 `GET /api/data`**
PRD 10번 참고. 쿼리파라미터 `limit`(기본 50) / `offset`(기본 0) / `start_date` / `end_date`.
`start_date <= date <= end_date` (양 끝 포함, PRD 10번 수정사항). 정렬: `date DESC`, 동일
날짜는 `created_at DESC`. 응답: `{"count": <조건에 맞는 전체 건수>, "items": [...]}`.

**3.4 `PUT /api/data/{id}`**
부분 수정 허용 (PRD 11번 — PUT이지만 body는 PATCH처럼 처리, 의도적 설계). 존재하지
않는 id → 404.

**3.5 `DELETE /api/data/{id}`**
존재하지 않는 id → 404. 성공 시 `{"deleted": true, "id": ...}`.

**3.6 `GET /api/data/summary`**
PRD 13번 응답 구조 그대로 구현. `analysis_service.py`에 계산 로직 분리.
**주의: `GET /api/data`의 페이지네이션된 목록을 재사용하지 말고, `data` 컬렉션 전체를
매번 다시 읽어서 계산한다** (1,116건 규모에서는 전체 스캔 비용이 크지 않음. limit/offset
이 걸린 일부 데이터로 summary를 계산하면 통계가 틀어진다).
- `total_income` = value>0 합계, `total_expense` = value<0 절댓값 합계, `net` = 차이
- `income_count`, `expense_count`
- `average_income` = total_income/income_count, `average_expense` = total_expense/expense_count
- `max_transaction`, `min_transaction`
- `current_month`: 데이터셋 내 최신 date가 속한 월 기준 income/expense/net
  (Task 테스트 케이스: 9월 거래를 추가하면 `current_month.month`가 "2026-09"로 바뀌는지
  반드시 확인 — PRD 13-1 참고)
- `trend`: Phase 4에서 구현할 `calculate_trend()` 호출 결과
- 이 `get_summary()` 함수는 Phase 6의 `/api/chat`에서도 그대로 재사용한다(같은 계산
  로직을 두 곳에 복붙하지 않기 — 값이 어긋나는 사고를 막는 가장 쉬운 방법).

**3.7 Swagger 테스트**
5개 엔드포인트 각각 정상 케이스 1개 + 존재하지 않는 id로 404 케이스 1개씩 확인.

---

### Phase 4. Trend 계산 로직

PRD 14번을 그대로 함수로 옮기는 작업. `analysis_service.py`에 `calculate_trend(records)`.

**4.1 월별 지출 집계**
각 월의 `abs(음수 value 합계)`. **거래가 없는 월은 0원으로 간주**(제외하지 않음 — PRD 14-1
수정사항, 분석 기간이 끊김 없는 1년 완결 데이터라는 전제).

**4.2 비교 구간**
"최근 3개월"은 오늘 날짜가 아니라 **데이터셋의 최신 거래일이 속한 월** 기준
(3-6의 `current_month`와 동일 기준일). 최근 3개월 평균 vs 그 이전 3개월 평균.

**4.3 변화율**
`(recent_avg - previous_avg) / previous_avg * 100`

**4.4 판정 기준**
```
-5% ~ +5%  → "유지"
+5% 초과   → "증가"
-5% 미만   → "감소"
```
문구 형식: `"최근 3개월 월평균 지출 {증가/감소} (+/-{n}%)"`. 유지인 경우 별도 문구
(예: "최근 3개월 지출이 비슷한 수준으로 유지되고 있어요").

**4.5 예외 처리 + 연결**
비교 가능한 월별 데이터가 부족하면(전체 6개월 미만) `"비교할 수 있는 충분한 월별
데이터가 없습니다."` 반환. 이전 기간 평균이 0원이면 일반 백분율 계산 대신 별도 문구
반환(0으로 나누기 방지). `GET /api/data/summary`의 `trend` 필드에 연결.

완료 기준: 실제 1,116건 데이터로 최근 3개월과 이전 3개월 각각의 월별 지출액·평균을
**직접 수동으로도 한 번 계산**해서 `calculate_trend()` 결과와 대조한다. 참고용 사전
계산값(코드에 박아넣지 말 것 — 어디까지나 "대략 이 근처가 맞다"는 검산용):
최근 3개월(6~8월) 평균 약 166만원, 이전 3개월(3~5월) 평균 약 119만원, 변화율 약 **+40%
증가**. 구현 결과가 이 근처(정확히 40.00%가 아니어도 큰 틀에서 "증가"이고 30~50%대)로
나오면 정상, "감소"나 한 자릿수 %가 나오면 로직을 의심할 것.

---

### Phase 5. 대화 기록 API

**5.1 Pydantic 모델**
```python
class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: str | None = None

class ConversationCreate(BaseModel):
    title: str | None = None
    messages: list[Message]
```

**5.2 `POST /api/conversations`**
PRD 15-1 참고. `title`이 비어있으면 첫 user 메시지로 자동 생성(30자 내외로 자름).
**⚠ 이 엔드포인트는 `/api/chat`의 자동저장과 별개다 — 프론트는 일반 채팅 흐름에서
이걸 호출하지 않는다** (PRD 15번 중복 저장 방지 규칙, Phase 8-3에서 다시 확인).

**5.3 `GET /api/conversations`**
메시지 본문 제외, 메타(`id`, `title`, `created_at`, `updated_at`, `message_count`)만 반환.
정렬: `updated_at DESC` — 마지막 메시지 시각 기준으로 최신 대화가 먼저 오게 한다
(PRD 16번). 대화를 이어가면(Phase 6) `updated_at`이 갱신되면서 목록 맨 위로 올라와야
정상이다.

**5.4 `GET /api/conversations/{id}`**
전체 `messages` 배열 포함 반환. 존재하지 않으면 404.

**5.5 `DELETE /api/conversations/{id}`**
존재하지 않으면 404.

**5.6 Swagger 테스트**
POST로 대화 하나 만들고 → GET 목록에서 보이는지 → GET/{id}로 전체 메시지 나오는지 →
DELETE 후 다시 GET/{id} 하면 404 뜨는지 순서대로 확인.

---

### Phase 6. AI 챗봇 API

**6.1 OpenAI 클라이언트 — ✅ 완료, 모델 확정: `gpt-5.5`**
`services/openai_service.py`. `OPENAI_MODEL` 환경변수로 모델명을 주입한다(코드
하드코딩 안 함). 클라이언트는 `openai.OpenAI(api_key=..., base_url=...)` — **`base_url`은
`OPENAI_BASE_URL` 환경변수에서 읽는다.** 코디세이가 제공하는 키(`sk-cody-live-`로
시작)는 프록시 전용이라, `base_url`을 안 넘기면 기본값인 `api.openai.com`으로
요청이 나가서 실패한다.

`/models` 엔드포인트로 확인한 프록시 지원 모델 11종: claude-haiku-4, claude-opus-4-7,
claude-opus-4-8, claude-sonnet-4, gemini-3-flash, gemini-3.1-flash-lite, gemini-3.1-pro,
gpt-5-mini, gpt-5.4, gpt-5.4-mini, **gpt-5.5**(채택). `gpt-5-mini`/`gpt-5.4-mini`가
더 저렴할 가능성이 있었지만, 이미 `gpt-5.5`로 6.7 통합 테스트까지 완료된 상태이고
개인 프로젝트라 트래픽이 적어 재검증 없이 유지하기로 결정했다(2026-09, 사용자 확인).

**6.2 시스템 프롬프트 조립**
PRD 22번 템플릿 그대로, `GET /api/data/summary` 응답 값을 f-string으로 채워넣는 함수
`build_system_prompt(summary: dict) -> str`.

**6.3 `POST /api/chat` 흐름**
PRD 19~21번 참고.
1. `conversation_id`가 없으면: 새 대화 생성 준비
2. 있으면: Firestore에서 해당 문서 조회 → **없으면 즉시 HTTP 404** ("대화를 찾을 수
   없습니다", PRD 20번 예외 규칙 — 조용히 새 대화로 대체하지 않는다)
3. `analysis_service.get_summary()`를 직접 호출해 최신 summary 재계산(캐싱 금지, 매
   요청마다) — 자기 자신의 `/api/data/summary` URL로 내부 HTTP 요청을 보내는 방식이
   아니라, 3.6에서 만든 함수를 그대로 import해서 쓴다.
4. 시스템 프롬프트 조립 → 기존 메시지 있으면 대화 이력 포함해서 GPT 호출
5. user/assistant 메시지를 Firestore에 append (신규면 새 문서 생성, 기존이면 `messages`
   배열에 추가 — 새 conversation을 만들지 않는다, PRD 20번 중요 규칙)
6. 응답: `{"conversation_id": ..., "reply": ..., "is_new_conversation": bool}`

**6.4 404 처리**
위 6.3의 2번 항목. Task 테스트 케이스: 존재하지 않는 `conversation_id`로 `/api/chat`
호출 → 404 확인. (새 대화로 조용히 대체되면 버그로 간주)

**6.5 GPT 호출 제한 및 오류 처리**
`max_tokens=500`(PRD 32번, 필요시 조정). 개발 중에는 실제 과금 발생하니 짧은 질문으로
먼저 확인. OpenAI 호출 자체가 실패하면(타임아웃 포함) 502로 응답하고, 원본 에러 메시지나
API 키는 응답에 노출하지 않는다(PRD 25번).

**6.6 자동 저장 — 저장 성공해야 정상 응답**
지난 라운드에서 "저장 실패해도 AI 답변은 보여주자"고 했던 걸 뒤집는다: 미션이 요구하는
"대화 내용 자동 저장"은 `/api/chat`의 핵심 계약이라, 저장이 실패했는데 200을 주면 사용자는
지금 화면엔 답변이 보이지만 나중에 "대화 기록"에 가보면 그 턴이 통째로 사라져 있는 걸
알게 된다 — 조용한 데이터 유실이라 오히려 더 나쁘다.
- Firestore 쓰기를 한 번 시도하고, 실패하면 1회 재시도(짧은 대기 후). 그래도 실패하면
  AI 답변을 버리고 **500**을 반환한다("답변을 저장하지 못했어요. 다시 시도해주세요") —
  이미 생성된 답변을 재사용하지 않고 그대로 실패로 처리해도 된다(이 프로젝트 규모에서
  Firestore 쓰기 실패는 드물게만 일어남 — 재시도 로직에 과도한 공수 들이지 않는다).
- 신규 대화면 새 문서 하나, 기존 대화면 같은 문서의 `messages` 배열에 추가(새 conversation을
  만들지 않는다 — PRD 20번). **기존 대화 저장 시 `updated_at`도 같이 갱신한다** — 안 하면
  5.3의 "최신 대화가 목록 맨 위" 정렬이 실제로 안 움직인다.

**6.7 통합 테스트**
PRD 23번 "기본 AI 질문" 4개(질문 1~3 + 저축 비교 질문 — PRD 23번에 4번째 질문 추가
반영 완료, 아래 참고)를 실제로 물어보고 답변에 실제 숫자가 들어가는지, 데이터에 없는
내용을 지어내지 않는지 확인. 존재하지 않는 `conversation_id`로 호출해 404가 나오는지도
같이 확인(6.4와 중복 확인이지만 실제 AI 흐름 안에서 한 번 더 검증).

---

### Phase 7. 백엔드 배포 (Render)

**7.1 requirements.txt**
로컬 가상환경에서 `pip freeze > requirements.txt`로 정확한 버전 고정.

**7.2 GitHub push**
`.env`, 서비스 계정 JSON, 원본 엑셀이 커밋에 안 들어갔는지 `git status`로 재확인 후 push.

**7.3 Render Web Service**
Root Directory: `backend` (기술스택.md 표 참고). Start Command:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**7.4 환경변수 등록**
Render 대시보드에 `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`,
`FIREBASE_SERVICE_ACCOUNT_JSON`, `ALLOWED_ORIGINS`(우선 `*`, Phase 9-4에서 좁힘) 5종 등록.

**7.5 배포 확인**
`https://<render-domain>/docs` 접속 확인. 첫 요청이 얼마나 느린지(콜드스타트) 직접
체감해볼 것 — 대략적인 대기 시간을 Phase 8-7 문구에 참고.

---

### Phase 8. 프론트엔드 개발

**8.1 폴더 이관**
`mockup/index.html`, `css/`, `js/`를 `frontend/`로 복사. `js/config.js` 신규 추가:
```js
const API_BASE_URL = "http://localhost:8000"; // 배포 시 Render 배포 URL로 직접 변경
```

**8.2 `api.js`**
fetch 공통 래퍼(`getJSON`, `postJSON`, `putJSON`, `deleteJSON`) — 매번 `fetch` 직접
쓰지 않고 여기 함수들로 통일. 에러 발생 시 상태코드별 처리(404/422/500 구분).

**8.3 채팅 화면**
목업의 정적 더미 메시지를 실제 `POST /api/chat` 호출로 교체. 요청 중 로딩 표시(PRD
33-1 필수 기능), 실패 시 오류 상태 표시, "새 대화" 버튼 클릭 시 `conversation_id`를
null로 리셋.

**8.4 데이터 관리 화면**
목업의 정적 테이블을 `GET /api/data`(페이지네이션 적용) 연동으로 교체. 추가/수정/삭제
모달은 목업 로직을 실제 API 호출로 교체(PUT/DELETE 포함 — PRD 33-2 "전체 CRUD UX 목표").

**8.5 대화 기록 화면**
`GET /api/conversations`로 목록, 클릭 시 `GET /api/conversations/{id}`로 전체 메시지
불러와서 표시. "이어서 질문하기" 시 해당 `conversation_id`를 채팅 화면에 전달.

**8.6 데이터 요약 화면**
`GET /api/data/summary` 연동, 목업의 실제 검증된 숫자 대신 라이브 데이터로 교체.

**8.7 콜드스타트 안내**
PRD 31번 문구를 API 요청 시작 시 노출, 응답 오면 숨김. 특히 첫 채팅 요청에서 반드시
보이는지 확인.

**8.8 로컬 통합 테스트**
`config.js`의 `API_BASE_URL`을 로컬 백엔드로 둔 채 브라우저에서 전체 화면 왔다갔다
하며 CORS 에러 없는지, 4개 화면 모두 실데이터로 동작하는지 확인.

---

### Phase 9. 프론트엔드 배포 + 통합 검증

**9.1~9.2** GitHub push → Vercel에서 프로젝트 임포트, **Root Directory: `frontend`**,
Framework Preset: **Other**(기술스택.md 표 참고, 빌드 커맨드 없음).

**9.3** `frontend/js/config.js`의 `API_BASE_URL`을 Render 배포 주소(https)로 **직접 수정해서
커밋·재배포**한다 — Vercel 환경변수 등록으로 대체하지 않는다. 바닐라 JS는 빌드 과정이
없어서, Vercel 환경변수는 빌드 스텝이 있어야 코드 안으로 치환되는데 우리는 그 빌드
자체가 없기 때문에 환경변수를 등록해봤자 `config.js`에 반영이 안 된다(Phase 3단계
목업 논의 때 짚었던 함정 — 여기서 실제로 막히기 쉬운 지점). 배포 후 브라우저 개발자
도구 Network 탭에서 실제 요청이 Render 주소로 가는지 확인할 것 — `localhost`가 남아있으면
실패.

**9.4** Render `ALLOWED_ORIGINS`를 실제 Vercel 도메인으로 좁히고 재배포.

**9.5** PRD 37번 체크리스트(필수 기능 14개 / AI 검증 7개 / 데이터 검증 6개 / 보안
검증 5개) 전체를 **배포된 URL 기준으로** 다시 확인.

**9.6** README.md(PRD 35번 항목 그대로: 서비스 소개/기술스택/배포 URL 3종/로컬
실행법/환경변수 목록/개인정보 처리)와 스크린샷 3종(PRD 36번: 요약이 보이는 채팅
화면, CRUD 동작이 보이는 데이터 관리 화면, 불러오기가 보이는 대화 기록 화면) 준비.

---

### Phase 10. 보너스 — Function Calling + MCP Server 연동

**바로잡음(2026-09-14)**: 이전 버전에 "Function Calling은 Phase 6에서 이미 구현·검증
완료"라고 적혀 있었는데 **사실이 아니다** — 검증 없이 쓴 문장이었다. Phase 6의
`/api/chat`은 요약을 텍스트로 시스템 프롬프트에 주입하는 방식뿐이고, `tools` 파라미터를
쓰는 실제 Function Calling은 여태 구현된 적이 없다. PRD 2번에도 애초에 "Function
Calling은 기본 기능 이후 보너스"라고 명시돼 있었다. 아래 10.1~10.2가 그 실제 구현이다.

미션 요구사항은 두 가지를 다 요구한다: (a) 챗봇 자체가 도구를 실제로 호출하는 것,
(b) **같은 기능**을 MCP Server 같은 외부 채널에서도 쓸 수 있게 하는 것. MCP만 만들고
(a)를 건너뛰면 미션 요구사항의 절반만 채우는 것이라 순서를 이렇게 정했다.

**10.1 `POST /api/chat`에 Function Calling 추가**
PRD 24-1의 `get_transaction_summary` 스키마(enum 포함) 그대로 OpenAI 클라이언트 호출에
`tools` 파라미터로 전달한다. 모델이 `tool_calls`를 반환하면: 해당 서비스 함수를 실제로
실행 → 결과를 다시 메시지 히스토리에 추가 → 모델을 한 번 더 호출해서 최종 답변을
받는다. 이 서비스 함수(`get_transaction_summary` 계산 로직)는 `analysis_service.py`에
새로 만들되, 기존 `get_summary()`/`calculate_trend()`를 내부적으로 재사용한다 — 로직을
중복 구현하지 않는다.

**10.2 통합 테스트**
PRD 24-3 흐름(질문 → 도구 필요성 판단 → 실제 호출 → Firestore 조회 → 결과 반영 →
최종 답변)이 실제로 일어나는지 확인한다. "1달 전엔 얼마 썼어?", "작년 11월엔 뭘 제일
많이 썼어?"로 테스트 — 지난 9월 13일에 배포된 서비스로 직접 확인했던, 기본 요약만으론
못 풀던 바로 그 질문들이다. 단순히 함수가 정의된 것만으로 PASS 처리하지 않는다 —
실제 tool_calls가 응답에 찍히는지 로그로 확인할 것.

**10.3 MCP 서버 마운트**
Python `mcp` SDK(Streamable HTTP transport)를 기존 `main.py`의 FastAPI 앱에 마운트한다.
새 Render 서비스를 만들지 않는다 — 같은 도메인 아래 새 경로(예: `/mcp`)로 노출한다.
정확한 마운트 방식은 이 시점 기준 `mcp` 패키지 공식 문서로 확인할 것(추측 금지).

**10.4 `get_transaction_summary`를 MCP tool로 노출**
10.1에서 만든 같은 서비스 함수를 MCP tool 핸들러에서도 그대로 호출한다 — 계산 로직을
또 새로 만들지 않는다.

**10.5 최소 인증**
공개 인터넷에 열리는 엔드포인트라 아무나 소비 데이터를 조회 못 하게 공유 비밀키를
요구하고 안 맞으면 401을 반환한다. 처음엔 요청 헤더(`X-MCP-Secret`)로 구현했었는데,
Claude.ai의 커스텀 헤더 인증(`static_headers`)이 조직(organization) 관리자용 beta
기능으로 보이고 무료/개인 플랜의 커스텀 커넥터 설정 화면엔 아예 안 뜰 가능성이 높다는
지적을 반영해 **URL 쿼리 파라미터 방식(`https://.../mcp?key=<MCP_SHARED_SECRET>`)**으로
바꿨다 — 커넥터 URL 입력창 하나만 있으면 되므로 플랜 상관없이 항상 된다. 접근 로그에
비밀키가 평문으로 남는 트레이드오프는 있지만, 개인용 조회 전용 API 1개 규모에서는
감수하기로 결정.

**10.6 환경변수 + 재배포**
`MCP_SHARED_SECRET` 환경변수를 Render에 추가 등록하고 재배포한다.

**10.7 Claude.ai 커넥터 연결 + 검증**
Claude.ai(무료 플랜 기준 커스텀 커넥터 1개 가능)에서 이 MCP 서버를 연결한다. 10.2와
같은 질문들로 실제 Claude.ai 대화창에서도 도구 호출이 일어나는지 확인한다.

**10.8 README 업데이트**
README에 Function Calling 흐름 + MCP 연동 방법을 정리한다(미션 요구사항: "어떤 근거로
어떤 도구를 호출했는지"와 호출 흐름 — 간단 다이어그램 또는 단계).

---

## 부록. 외부(GPT) 검토 반영 기록

이 Task.md는 외부 검토를 한 차례 거쳤다. 아래는 무엇을 받아들이고 무엇을 거절했는지에
대한 기록이다 (다음에 또 다른 검토가 들어오면 왜 이렇게 정리했는지 참고할 것).

**받아들인 것**
- `openpyxl` 패키지 누락 (1.3) — 실제로 없으면 xlsx를 못 읽는 진짜 버그였음
- category 미매핑 시 `null` 처리, sign 기반 추측 금지 (2.3) — 확인 안 된 분류를 만들어내지 않는 게 맞음
- 초기 적재 재실행 방지 가드 (2.4) — 단, 트랜잭션/락 구조는 과함, 단순 체크로 충분
- summary는 페이지네이션된 목록이 아니라 전체 컬렉션을 다시 읽어야 함 (3.6) — 통계가 틀어질 수 있는 진짜 버그였음
- PRD 23번 기본 질문 개수 불일치 발견 (6.7) — 단, "4개→3개"가 아니라 **PRD 23번에 누락된
  4번째 질문을 추가**하는 쪽으로 바로잡음 (시나리오.md 재분류와 동기화가 원래 맞는 방향)
- 저장 실패 시 AI 답변만 보여주고 넘어가는 정책 폐기 (6.6) — 자동 저장은 미션의 핵심 계약이라,
  조용히 유실되는 것보다 실패를 명확히 알리는 게 맞음
- Vercel 환경변수로 API_BASE_URL을 설정한다는 원래의 애매한 대안을 제거하고 config.js
  직접 수정·커밋으로 단일화 (9.3) — 무빌드 정적 사이트에서는 애초에 성립하지 않는 방법이었음

**거절하거나 축소한 것**
- `tests/` 폴더 + pytest 스타일의 방대한 합성 데이터 검증 매트릭스(윤년, ±5% 정확한 경계,
  타임존 등) — 기술스택.md에서 이미 "자동 테스트 생략, Swagger 수동 확인으로 충분"이라고
  정한 부분과 정면으로 충돌한다. 개별 지적은 다 맞는 말이지만, 전부 받아들이면 비전공자가
  혼자 감당하기 어려운 프로덕션급 QA 프로젝트가 되어버린다.
- 대화 저장에 낙관적 동시성 제어(버전 체크, 409 Conflict) 도입 — 이 앱은 사용자 1명이
  쓰는 개인 프로젝트다. 같은 대화에 동시에 두 탭에서 메시지를 보내는 상황은 현실적으로
  거의 없고, 생겨도 "마지막에 쓴 게 이긴다" 정도로 충분하다. 버전 관리 로직을 새로 넣을
  만큼의 실익이 없다고 판단했다.
- 대화 저장에 초기 적재용 `import_runs` 추적 문서 + Firestore 트랜잭션 락 — 이 스크립트는
  개발자 본인이 로컬에서 딱 한 번 수동 실행하는 것이다. "이미 데이터가 있으면 중단"
  정도의 단순 가드로 충분하고, 동시 실행 방지까지 만들 필요는 없다.
- 502/503/504/409 등 세분화된 에러 코드 체계 전체 도입 — OpenAI 호출 실패에 502를 쓰는 것
  정도는 받아들였지만(6.5), 나머지는 PRD 25번이 정한 "422/404/500" 선을 넘어서는 과설계라
  최소한만 반영했다.
- 메시지 배열 크기 제한(100개/500KiB) 같은 세부 방어 로직 — 이 규모의 개인 대화 앱에서
  실제로 걸릴 일이 거의 없는 제한이라 지금 단계에서는 넣지 않는다. 필요해지면 그때 추가한다.
