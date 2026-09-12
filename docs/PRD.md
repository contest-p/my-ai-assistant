# PRD.md — 전역 후 1년, 내 소비를 아는 AI 비서

> **문서 목적**  
> `시나리오.md`의 사용자 경험과 미션 요구사항을 실제 데이터 구조, API, AI 동작 방식으로 확정한다.  
> 본 문서를 기준으로 Task를 작성하고 개발한다.

---

# 1. 제품 개요

## 1-1. 제품명

**전역 후 1년, 내 소비를 아는 AI 비서**

## 1-2. 한 줄 설명

2025.08.18 ~ 2026.08.18의 KB국민은행 거래내역을 기반으로 사용자의 소비·저축 패턴을 분석하고 자연어로 답변하는 개인 재정 AI 비서.

## 1-3. 핵심 사용자

전역 후 사회 복귀를 준비하는 사용자 본인.

## 1-4. 핵심 가치

사용자가 지난 1년간 흩어져 있던 금융 거래를 직접 확인하고, AI에게 자연어로 질문하여 소비·수입·추세를 이해할 수 있도록 한다.

---

# 2. 미션 요구사항 반영 범위

본 제품은 미션의 다음 필수 기능을 모두 구현한다.

1. 데이터 기반 AI 채팅
2. 데이터 CRUD
3. 데이터 요약
4. 대화 기록 저장/목록/불러오기/삭제
5. FastAPI + Firestore + OpenAI 기반 백엔드
6. HTML/CSS/JavaScript 기반 프론트엔드
7. Render 백엔드 배포
8. Vercel 프론트엔드 배포
9. README 및 제출 스크린샷

선택 사항인 Function Calling 및 추가 UX 기능은 기본 기능 구현 이후 보너스로 진행한다.

---

# 3. 원본 데이터

## 3-1. 데이터 출처

- 원본: KB국민은행 거래내역조회 엑셀
- 분석 기간: 2025.08.18 ~ 2026.08.18
- 총 거래 건수: 1,116건
- 출금: 862건
- 입금: 254건

## 3-2. 원본 주요 컬럼

- 거래일시
- 적요
- 보낸분/받는분
- 송금메모
- 출금액
- 입금액
- 잔액
- 거래점

## 3-3. 개인정보 처리 원칙

원본 데이터에는 계좌정보, 잔액, 거래 상대방의 실명 등 민감정보가 포함될 수 있으므로 다음 원칙을 적용한다.

- 원본 KB 엑셀은 GitHub 저장소에 업로드하지 않는다.
- 애플리케이션에는 비식별화된 파생 데이터만 사용한다.
- `memo`에는 거래 상대방의 개인 실명을 저장하지 않는다.
- README 및 제출 스크린샷에서도 개인 식별 정보가 노출되지 않도록 마스킹한다.
- API Key 및 Firebase 서비스 계정 정보는 코드에 하드코딩하지 않는다.

---

# 4. 데이터 매핑 및 스키마

## 4-1. `value` 정의

거래 데이터의 `value`는 **거래건별 순액**으로 정의한다.

```text
입금 → 양수(+)
지출 → 음수(-)
```

예:

```text
월급 입금 3,000,000원 → +3,000,000
편의점 지출 4,600원 → -4,600
```

### 채택 이유

- CRUD를 통한 수동 거래 추가가 직관적이다.
- 사용자가 "5,000원을 썼다"라는 거래를 바로 `-5000`으로 입력할 수 있다.
- 잔액을 value로 사용할 경우 신규 거래 입력이나 기존 거래 수정 시 이후 잔액이 연쇄적으로 변경되는 문제가 있다.

---

# 5. 수입·지출 계산 규칙

`value`의 부호를 기준으로 수입과 지출을 명확하게 분리한다.

## 5-1. 총 수입

양수 value의 합계.

```text
total_income = Σ(value > 0)
```

## 5-2. 총 지출

음수 value의 절댓값 합계.

```text
total_expense = Σ(abs(value)) for value < 0
```

## 5-3. 순증감

```text
net = total_income - total_expense
```

따라서 `total_income`, `total_expense`는 항상 0 이상이고, `net`만 음수가 될 수 있다.

---

# 6. 데이터 컬렉션

Firestore 컬렉션명:

```text
data
```

## 6-1. 거래 문서 스키마

| 필드 | 타입 | 필수 | 설명 |
|---|---|---:|---|
| id | string | 자동 | Firestore 문서 ID |
| date | string | O | `YYYY-MM-DD` |
| value | number | O | 순액. 입금 + / 지출 - |
| memo | string | O | 비식별화된 거래 내용 |
| category | string | 선택 | 거래 분류 |
| created_at | timestamp | 자동 | 서버 저장 시각 |

### 예시

```json
{
  "id": "d_a1b2c3",
  "date": "2026-08-18",
  "value": -4600,
  "memo": "체크카드 결제 · 편의점",
  "category": "카드결제",
  "created_at": "2026-09-08T10:00:00Z"
}
```

---

# 7. Category 정의

`category`는 기본 CRUD의 핵심 필수 입력값이 아니라 **분석 및 Function Calling 보너스용 분류 정보**다.

## 7-1. 초기 category 매핑

| 원본 적요 | category |
|---|---|
| 체크카드, 국민카드, 카드입금 | 카드결제 |
| 오픈뱅킹출금, 전자금융, CMS 공동, FBS출금/입금, 뱅크페이 | 계좌이체 |
| 현금IC | 현금인출 |
| 급여입금 | 급여 |
| 결산이자 | 이자 |
| 스마트입금, 센타입금 | 기타입금 |

세부 매핑은 Task 단계에서 실제 1,116건을 확인한 후 확정한다.

---

# 8. Conversations 컬렉션

Firestore 컬렉션명:

```text
conversations
```

## 8-1. 문서 스키마

| 필드 | 타입 | 필수 | 설명 |
|---|---|---:|---|
| id | string | 자동 | Firestore 문서 ID |
| title | string | O | 대화 제목 |
| messages | array | O | 전체 대화 메시지 |
| created_at | timestamp | 자동 | 생성 시각 |
| updated_at | timestamp | 자동 | 마지막 메시지 시각 |

## 8-2. message 구조

```json
{
  "role": "user",
  "content": "이번 달 지출이 많아?",
  "timestamp": "2026-09-08T10:00:00Z"
}
```

`role`은 최소 다음 값을 허용한다.

```text
user
assistant
```

---

# 9. 데이터 API

## 9-1. POST `/api/data`

거래 데이터를 추가한다.

### Request

```json
{
  "date": "2026-08-18",
  "value": -4600,
  "memo": "체크카드 결제 · 편의점",
  "category": "카드결제"
}
```

### 필수 입력

- date
- value
- memo

`category`는 선택 입력이다.

### Response

HTTP `201`

```json
{
  "id": "d_a1b2c3",
  "date": "2026-08-18",
  "value": -4600,
  "memo": "체크카드 결제 · 편의점",
  "category": "카드결제",
  "created_at": "2026-09-08T10:00:00Z"
}
```

---

# 10. GET `/api/data`

거래 데이터를 조회한다.

## Query Parameters

```text
limit      기본값 50
offset     기본값 0
start_date 선택
end_date   선택
```

`start_date <= date <= end_date` — **양 끝 날짜를 모두 포함(inclusive)한다.** SQL의 `BETWEEN`과
동일한 의미로, `end_date`를 배타적(exclusive)으로 잘못 구현하기 쉬워 명시해둔다.

## 정렬 기준

기본적으로 최신 거래가 먼저 나오도록 `date DESC` 기준으로 정렬한다.

동일 날짜에서는 `created_at DESC`를 사용한다.

## Response

```json
{
  "count": 1116,
  "items": [
    {
      "id": "d_a1b2c3",
      "date": "2026-08-18",
      "value": -4600,
      "memo": "체크카드 결제 · 편의점",
      "category": "카드결제"
    }
  ]
}
```

`count`는 검색 조건에 해당하는 전체 건수를 의미한다.

---

# 11. PUT `/api/data/{id}`

기존 거래를 수정한다.

## Request

부분 수정(PATCH와 유사한 방식)을 허용한다.

> REST 의미상으로는 PATCH가 더 맞지만, 미션이 `PUT /api/data/{id}`를 명시적으로 요구하므로
> 엔드포인트는 PUT을 그대로 쓰고 body만 부분 수정으로 처리한다 (의도적 설계, 수정 대상 아님).

```json
{
  "value": -5000,
  "memo": "체크카드 결제 · 편의점(수정)"
}
```

수정 가능한 필드:

- date
- value
- memo
- category

## Response

HTTP `200`

수정된 전체 문서를 반환한다.

존재하지 않는 ID는 HTTP `404`.

---

# 12. DELETE `/api/data/{id}`

거래를 삭제한다.

## Response

HTTP `200`

```json
{
  "deleted": true,
  "id": "d_a1b2c3"
}
```

존재하지 않는 ID는 HTTP `404`.

---

# 13. GET `/api/data/summary`

AI 프롬프트 주입에 사용할 요약 정보를 반환한다.

## Response 구조

```json
{
  "period": "2025-08-18 ~ 2026-08-18",
  "count": 1116,
  "metrics": {
    "total_income": 30470405,
    "total_expense": 30243572,
    "net": 226833,
    "income_count": 254,
    "expense_count": 862,
    "average_income": 119962,
    "average_expense": 35085,
    "max_transaction": 4767952,
    "min_transaction": -89700
  },
  "current_month": {
    "month": "2026-08",
    "income": 1703286,
    "expense": 1868120,
    "net": -164834
  },
  "trend": "최근 3개월 월평균 지출 증가 (+40%)"
}
```

> 위 `trend` 값은 실제 1,116건으로 계산한 참고 방향이다(6~8월 평균이 3~5월 평균보다
> 높게 나옴). TASK 4.5에서 이 값을 검산 기준으로 다시 대조하되, 정확한 소수점까지
> 일치할 필요는 없다 — "증가" 방향과 대략적인 크기(30~50%대)만 맞으면 정상이다.

> **수정 1 — `transaction_average` 제거**: 입금·지출을 부호 그대로 섞어 평균 내면(원래 값 203원)
> 실사용 의미가 없다. "평균적으로 얼마씩 써?" 질문에 그대로 답하면 왜곡된 숫자가 나간다.
> `average_income`(119,962원) / `average_expense`(35,085원)로 분리하고, 이를 계산하는 데
> 필요한 `income_count`/`expense_count`도 함께 반환한다.
>
> **수정 2 — `current_month` 추가**: 기존 스펙엔 "이번 달" 수치가 없어서 시나리오.md의
> "이번 달 지출이 평소보다 많은 편이야?" 질문에 AI가 근거로 쓸 정확한 숫자가 없었다.
> 데이터셋 내 최신 날짜가 속한 월(현재는 2026-08, CRUD로 거래가 추가되면 자동 갱신)을
> 기준으로 그 달의 수입/지출/순증감을 별도 집계한다.

## 13-1. summary 계산 규칙

### period

전체 데이터의 최소 날짜와 최대 날짜를 표시한다.

### count

전체 거래 건수.

### total_income

양수 value 합계.

### total_expense

음수 value 절댓값 합계.

### net

`total_income - total_expense`.

### income_count / expense_count

`value`가 양수/음수인 거래 건수 각각.

### average_income

```text
total_income / income_count
```

### average_expense

```text
total_expense / expense_count
```

### max_transaction

전체 거래 중 가장 큰 `value`.

### min_transaction

전체 거래 중 가장 작은 `value`.

### current_month

데이터셋 내 최신 날짜가 속한 월을 기준으로 그 달의 income/expense/net을 별도 집계한다.
매 요청마다 재계산한다(캐싱 금지) — CRUD로 거래가 추가되면 즉시 반영되어야 하기 때문이다.

**Task 단계 테스트 케이스**: 현재 데이터 최신월은 2026-08이라 `current_month.month`가
`"2026-08"`이다. 만약 `2026-09-05` 날짜로 새 거래를 추가하면, 그 즉시(다음 `/api/data/summary`
호출부터) `current_month.month`가 `"2026-09"`로 바뀌고 income/expense/net도 9월 거래만
반영해서 다시 계산돼야 한다. 이 케이스를 Task.md에 명시적으로 넣어둘 것.

---

# 14. Trend 계산 규칙

거래 단위 `value`를 직접 추세 계산에 사용하지 않는다.

거래 데이터를 월별로 집계한 뒤 **월별 총 지출액**을 기준으로 추세를 계산한다.

## 14-1. 월별 지출액

각 월의 음수 거래 value 절댓값 합계를 해당 월의 지출액으로 정의한다.

```text
월별 지출액 = abs(해당 월의 음수 value 합계)
```

**해당 월에 거래가 하나도 없으면 그 달의 지출액은 0원으로 간주한다** (분석 기간 전체가
끊김 없이 이어진 1년치 완결 데이터라는 전제 — 데이터가 잘려서 없는 게 아니라 실제로 거래가
없었던 것으로 본다). 비교 구간을 제외 처리하지 않는다.

## 14-2. 비교 구간

**"최근 3개월"은 오늘 날짜가 아니라 데이터셋에 존재하는 최신 거래일이 속한 월을 기준으로
한다** (13번 `current_month`와 동일한 기준일). CRUD로 새 거래가 추가되면 이 기준월도
자동으로 갱신된다.

최근 3개월의 월별 총 지출액 평균과 그 이전 3개월의 월별 총 지출액 평균을 비교한다.

```text
recent_avg = 최근 3개월 월별 지출 평균
previous_avg = 그 이전 3개월 월별 지출 평균
```

## 14-3. 변화율

```text
change_rate =
(recent_avg - previous_avg) / previous_avg × 100
```

## 14-4. 판정 기준

```text
-5% ≤ change_rate ≤ +5% → 유지
change_rate > +5%       → 증가
change_rate < -5%       → 감소
```

예:

```text
최근 3개월 평균 지출이 이전 3개월 대비 8% 감소
→ "최근 3개월 월평균 지출 감소 (-8%)"
```

### 예외 처리

비교 대상 기간의 지출 데이터가 부족하여 유효한 비교가 불가능한 경우:

```text
"비교할 수 있는 충분한 월별 데이터가 없습니다."
```

를 반환한다.

0원인 이전 기간을 기준으로 변화율을 계산해야 하는 경우에는 일반적인 백분율 비교를 하지 않고 별도 예외 문구를 반환한다.

---

# 15. 대화 기록 API

## 15-1. POST `/api/conversations`

대화를 새로 저장한다.

> **⚠ 중복 저장 방지 규칙**: `/api/chat`은 20번 흐름에서 이미 대화를 자동으로 저장한다.
> **프론트엔드는 `/api/chat`으로 이미 자동 저장된 대화를 다시 `POST /api/conversations`로
> 저장하지 않는다.** 이 엔드포인트는 (a) 미션이 요구하는 별도 API로서 Swagger에서
> 존재를 확인/테스트할 수 있어야 하고, (b) 향후 채팅 흐름 밖에서 대화를 수동으로
> 백업/가져오기 하는 경우에만 프론트에서 호출한다. 일반 채팅 사용 중에는 호출되지 않는다.

### Request

```json
{
  "title": "이번 달 지출 분석",
  "messages": [
    {
      "role": "user",
      "content": "이번 달 실적이 어때?"
    },
    {
      "role": "assistant",
      "content": "이번 달 지출은..."
    }
  ]
}
```

`title`이 비어 있으면 첫 사용자 질문을 기반으로 자동 생성한다.

### Response

HTTP `201`

```json
{
  "id": "c_x1y2z3",
  "title": "이번 달 지출 분석",
  "created_at": "2026-09-08T10:00:00Z",
  "message_count": 2
}
```

---

# 16. GET `/api/conversations`

대화 목록을 조회한다.

메시지 본문은 반환하지 않고 메타정보만 반환한다.

### Response

```json
{
  "count": 12,
  "items": [
    {
      "id": "c_x1y2z3",
      "title": "이번 달 지출 분석",
      "created_at": "2026-09-08T10:00:00Z",
      "updated_at": "2026-09-08T10:05:00Z",
      "message_count": 2
    }
  ]
}
```

정렬: `updated_at DESC`. 마지막 메시지 시각 기준으로 최신 대화를 먼저 표시한다.
기존 대화를 이어가면 20번의 `updated_at` 갱신 규칙에 따라 목록 순서에도 반영한다.

---

# 17. GET `/api/conversations/{id}`

특정 대화 전체를 불러온다.

### Response

```json
{
  "id": "c_x1y2z3",
  "title": "이번 달 지출 분석",
  "created_at": "2026-09-08T10:00:00Z",
  "updated_at": "2026-09-08T10:05:00Z",
  "messages": [
    {
      "role": "user",
      "content": "이번 달 실적이 어때?",
      "timestamp": "2026-09-08T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "이번 달 지출은...",
      "timestamp": "2026-09-08T10:00:01Z"
    }
  ]
}
```

존재하지 않는 ID는 HTTP `404`.

---

# 18. DELETE `/api/conversations/{id}`

특정 대화를 삭제한다.

### Response

```json
{
  "deleted": true,
  "id": "c_x1y2z3"
}
```

존재하지 않는 ID는 HTTP `404`.

---

# 19. POST `/api/chat`

사용자의 질문을 받아 데이터 기반 AI 답변을 생성한다.

## Request

```json
{
  "message": "이번 달 실적이 어때?",
  "conversation_id": null
}
```

`conversation_id`가 null이면 새 대화다.

---

# 20. `/api/chat` 처리 흐름

## 신규 대화

```text
사용자 질문
 ↓
summary 최신 조회
 ↓
시스템 프롬프트 생성
 ↓
GPT 호출
 ↓
conversation 생성
 ↓
user message 저장
 ↓
assistant message 저장
 ↓
응답 반환
```

## 기존 대화

```text
사용자 질문
 ↓
summary 최신 조회
 ↓
기존 conversation 조회
 ↓
기존 messages + 신규 user message 구성
 ↓
시스템 프롬프트 생성
 ↓
GPT 호출
 ↓
기존 conversation에 user/assistant message 추가
 ↓
updated_at 갱신
 ↓
응답 반환
```

### 중요 규칙

`conversation_id`가 기존 대화를 가리키는 경우 **새 conversation을 생성하지 않는다.**

반드시 기존 문서의 `messages` 배열에 새 메시지를 추가한다.

### 예외 규칙 (누락됐던 케이스)

`conversation_id`가 주어졌지만 Firestore에 해당 문서가 없는 경우(삭제된 대화 등):

```text
HTTP 404, "대화를 찾을 수 없습니다"
```

이때 새 conversation으로 조용히 대체하지 않는다. PUT/DELETE의 404 처리와 일관성을 유지하고,
프론트가 "대화가 사라졌다"는 상황을 사용자에게 명확히 알릴 수 있게 하기 위함이다.

---

# 21. `/api/chat` Response

```json
{
  "conversation_id": "c_new123",
  "reply": "이번 달 현재까지 약 42만원을 썼습니다.",
  "is_new_conversation": true
}
```

기존 대화라면:

```json
{
  "conversation_id": "c_x1y2z3",
  "reply": "지난 질문과 비교하면...",
  "is_new_conversation": false
}
```

---

# 22. AI 시스템 프롬프트

```text
당신은 사용자의 개인 재정을 분석해주는 AI 비서입니다.

[사용자 데이터 요약]
- 데이터 기간: {period}
- 총 거래 건수: {count}건 (입금 {income_count}건 / 지출 {expense_count}건)
- 총 수입: {total_income}원 / 총 지출: {total_expense}원 / 순증감: {net}원
- 평균 입금액: {average_income}원 / 평균 지출액: {average_expense}원
- 최대 거래: {max_transaction}원 / 최소 거래: {min_transaction}원
- 이번 달({current_month.month}) 수입: {current_month.income}원 / 지출: {current_month.expense}원
- 최근 추세: {trend}

위 데이터를 기반으로 친근하고 구체적으로 답변하세요.

답변 규칙:
1. 가능한 경우 실제 데이터를 숫자로 인용하세요.
2. 데이터에 없는 사실은 임의로 추측하지 마세요.
3. 사용자의 질문과 관련된 데이터만 선택적으로 활용하세요.
4. "총 얼마 썼어?" 같은 질문에는 total_expense를 기준으로 답하세요.
5. "이번 달 얼마 썼어? / 평소보다 많아?" 같은 질문에는 current_month와 trend를 함께 활용하세요.
6. "수입과 지출 차이가 얼마야? / 저축은 잘 하고 있어?" 같은 질문에는 net을 기준으로 답하세요.
7. "평균적으로 얼마씩 써?"에는 average_expense를, "평균적으로 얼마씩 받아?"에는 average_income을 쓰고 서로 혼동하지 마세요.
8. 월별 추세 질문에는 trend 정보를 활용하세요.
```

---

# 23. 기본 AI 질문

다음 질문은 **기본 미션 검증용 대표 시나리오**로 사용한다.

### 질문 1

```text
전역하고 나서 지금까지 총 얼마 썼어?
```

기대 동작:

- `total_expense`를 활용
- 총 지출액을 숫자로 답변

### 질문 2

```text
이번 달 지출이 평소보다 많은 편이야?
```

기대 동작:

- 현재 월의 지출 데이터와 summary의 추세 정보를 활용
- 가능한 범위에서 비교 근거를 제시

### 질문 3

```text
월별로 지출 추세가 어떻게 변했는지 알려줘
```

기대 동작:

- 월별 지출 집계 기준을 사용
- 증가/감소/유지 추세 설명

### 질문 4

```text
입금이랑 지출 비교하면 저축은 잘 하고 있는 편이야?
```

기대 동작:

- `net`을 활용 (기본 요약에 이미 포함되어 있어 Function Calling 불필요 — 시나리오.md에서
  보너스로 오분류했던 걸 기본으로 재분류한 결정과 동기화)
- 수입/지출 차이를 근거로 답변

---

# 24. Function Calling 보너스 설계

Function Calling은 기본 미션 완료 이후 구현한다.

## 24-1. Tool 1 — 카테고리별 지출 조회

Tool 이름:

```text
get_category_expense
```

> **검토자 피드백에 대한 판단**: "체크카드"(사용자 언어) vs "카드결제"(내부 category
> 값)가 다르다는 지적은 맞다. 다만 제안받은 해결책(예시 질문을 "카드결제로 얼마를 가장
> 많이 썼어?"로 바꾸기)은 채택하지 않는다 — 사용자가 앱 내부 분류명을 그대로 말해야만
> 동작하는 건 자연어 챗봇 취지에 안 맞는다. Function Calling의 존재 이유 자체가
> "사용자의 일상 언어 → 구조화된 파라미터" 매핑을 GPT가 해주는 것이므로, 이 매핑은
> 질문을 바꿔서 피할 게 아니라 **tool 스키마 안에서 해결**한다: enum 각 값에 설명을
> 붙여서 GPT가 "체크카드"를 보고도 "카드결제"를 정확히 고르게 하고, `category`를
> 선택 파라미터로 바꿔서 "제일 많이 나간 게 뭐야?"류 순위 질문은 애초에 매핑이
> 필요 없게 만든다 (아래 참고).

### Input

```json
{
  "category": "카드결제"
}
```

`category`는 **선택 파라미터**이며, 값을 줄 경우 7-1 매핑표의 값만 허용하는 **enum**으로
선언한다 (자유 문자열 금지 — GPT가 존재하지 않는 카테고리명을 지어내 조회하는 것을 방지).
OpenAI function calling의 `strict` 모드로 enum을 강제하면 이 값 외에는 애초에 응답 자체가
생성되지 않는다.

각 enum 값에는 GPT가 사용자 언어와 매핑할 수 있도록 설명을 함께 등록한다:

| enum 값 | 설명 (tool schema의 description) |
|---|---|
| `카드결제` | 체크카드·신용카드·국민카드로 결제한 거래 |
| `계좌이체` | 오픈뱅킹·전자금융 등 계좌 간 이체 |
| `현금인출` | ATM 등 현금 출금 |
| `급여` | 급여 입금 |
| `이자` | 결산이자 입금 |
| `기타입금` | 위에 해당하지 않는 입금 |

`category`를 **생략하면** 전체 카테고리를 지출액 기준 내림차순으로 집계해 반환한다
(아래 Output 두 번째 예시). "제일 많이 나간 게 뭐야?" 같은 순위 질문은 GPT가 특정
카테고리를 먼저 골라야 하는 부담 없이 이 방식으로 한 번의 호출로 답할 수 있다.

### Output

카테고리 지정 시:

```json
{
  "category": "카드결제",
  "total_expense": 123456,
  "count": 87
}
```

카테고리 생략 시 (전체 랭킹):

```json
{
  "breakdown": [
    { "category": "카드결제", "total_expense": 21345000, "count": 601 },
    { "category": "계좌이체", "total_expense": 8000000, "count": 210 },
    { "category": "현금인출", "total_expense": 800000, "count": 13 }
  ]
}
```

### 사용 예

```text
체크카드로 제일 많이 나간 게 뭐야?
```

기대 호출: `category` 생략 → 전체 랭킹에서 1위 항목(카드결제)을 근거로 답변.
(만약 "체크카드로 이번 달 얼마 썼어?"처럼 특정 카테고리를 지정해야 하는 질문이면,
enum 설명을 근거로 `category: "카드결제"`를 채워서 호출한다.)

## 24-2. Tool 2 — 기간별 조회

> **원래 설계였던 `get_income_expense_summary`는 제거한다.** 13번 섹션에서
> `total_income`/`total_expense`/`net`이 이미 매 `/api/chat` 요청마다 시스템 프롬프트에
> 통째로 주입되므로, GPT는 이 도구를 호출하기 전부터 답을 이미 알고 있다. 즉 정의는 되어도
> **실제로는 절대 호출되지 않는다** — 24-3의 "Function Calling이 실제로 발생"이라는 검증
> 기준을 통과할 수 없다. (참고로 "저축은 잘 하고 있어?" 질문도 이 데이터로 기본 요약만으로
> 답변 가능하므로, 시나리오.md에서 이 질문을 보너스로 분류했던 것 자체가 재분류 대상이다 —
> 아래 답변 하단 참고.)
>
> 대신 기본 요약(고정된 전체 기간 + 이번 달)에 없는 정보, 즉 **임의 기간 조회**를 제공한다.

Tool 이름:

```text
get_period_summary
```

### Input

```json
{
  "start_date": "2026-08-01",
  "end_date": "2026-08-07"
}
```

10번 섹션과 동일하게 `start_date <= date <= end_date` (양 끝 포함).

### Output

```json
{
  "start_date": "2026-08-01",
  "end_date": "2026-08-07",
  "income": 0,
  "expense": 215000,
  "net": -215000,
  "count": 14
}
```

### 사용 예

```text
지난주엔 얼마 썼어?
11월엔 얼마 썼어?
```

("이번 달" 질문은 13번의 `current_month`로 기본 요약만으로 이미 답변되므로, 이 도구는
그 외의 임의 기간 질문에서만 실제로 호출된다.)

## 24-3. 보너스 검증 기준

단순히 함수가 존재하는 것으로 PASS하지 않는다.

다음 흐름이 실제로 확인되어야 한다.

```text
사용자 질문
 ↓
GPT가 Tool 필요성 판단
 ↓
Function Calling 발생
 ↓
Backend Tool 실행
 ↓
Firestore 조회
 ↓
Tool 결과 GPT 전달
 ↓
최종 답변
```

---

# 25. Validation / 입력값 검증

Pydantic을 사용하여 API 요청 데이터를 검증한다.

## 데이터 검증

### date

```text
YYYY-MM-DD
```

형식만 허용한다.

### value

숫자 타입이어야 한다.

### memo

빈 문자열을 허용하지 않는다.

### category

정해진 category 값이 아닌 경우 정책을 명확히 적용한다.

기본적으로 유연한 문자열을 허용하되 초기 데이터는 정의된 category를 사용한다.

## 오류

잘못된 요청:

```text
HTTP 422
```

존재하지 않는 ID:

```text
HTTP 404
```

예상하지 못한 서버 오류:

```text
HTTP 500
```

`/api/chat`은 대화 저장에 성공해야 정상 응답한다. 저장 실패 시 1회 재시도하고,
계속 실패하면 AI 답변 대신 HTTP 500과 저장 실패 안내를 반환한다.
OpenAI 호출 자체의 실패(타임아웃 포함)에만 HTTP 502를 적용한다.

단, 외부 API의 민감한 내부 오류나 API Key 등은 응답에 노출하지 않는다.

---

# 26. CORS

개발 중:

```text
*
```

허용 가능.

배포 직전에는:

```text
ALLOWED_ORIGINS
```

를 사용하여 Vercel 프론트엔드 도메인만 허용한다.

---

# 27. 환경 변수

백엔드 환경변수는 다음 5종을 사용한다.

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
FIREBASE_SERVICE_ACCOUNT_JSON
ALLOWED_ORIGINS
```

`OPENAI_BASE_URL`은 코디세이가 제공하는 프록시 엔드포인트(`https://copa.codyssey.kr/v1`)
주소다. OpenAI 클라이언트 초기화 시 `base_url` 파라미터로 넘긴다 — 이게 없으면 기본값인
`api.openai.com`으로 요청이 나가서 실패한다 (`OPENAI_API_KEY`가 `sk-cody-live-`로
시작하는 프록시 전용 키이기 때문).

`OPENAI_MODEL` 환경변수로 모델명을 주입한다. 실제 모델명은 AI 연동 구현 시점에
결정하며, 코드에 하드코딩하지 않는다. 단, 이 프록시가 지원하는 모델 목록이 일반
OpenAI API와 다를 수 있으므로 Phase 6에서 실제로 확인 후 결정한다.

프론트 설정값: `frontend/js/config.js`의 `API_BASE_URL`. Render 배포 URL로 직접
변경한 후 커밋·재배포한다. 이 공개 API 주소는 백엔드 환경변수와 구분한다(빌드 과정이
없는 바닐라 JS라 Vercel 환경변수로는 주입되지 않음 — 9번 Task 9-3 참고).

백엔드 환경변수 값은 GitHub에 커밋하지 않는다.

`.env`는 `.gitignore`에 포함한다.

Firebase 서비스 계정 JSON 역시 저장소에 직접 업로드하지 않는다.

---

# 28. Firestore 접근 원칙

서버에서 Firebase Admin SDK를 사용한다.

Firestore 컬렉션:

```text
data
conversations
```

원본 Excel 파일을 Firestore에 저장하지 않는다.

애플리케이션에는 전처리된 거래 레코드만 저장한다.

---

# 29. 초기 데이터 적재

## 입력

```text
KB_거래내역_비식별화.xlsx
```

## 변환

```text
date
value
memo
category
```

형태로 변환한다.

## 적재

변환 결과를 Firestore `data` 컬렉션에 bulk upload한다.

### 초기 검증 기준

적재 후:

```text
총 거래 건수 = 1,116건
```

이어야 한다.

또한:

```text
입금 + 출금 = 1,116건
```

인지 확인한다.

엑셀 원본 자체는 GitHub 저장소에 넣지 않는다.

---

# 30. 페이지네이션

`GET /api/data`는 기본적으로 페이지네이션을 사용한다.

```text
limit = 50
offset = 0
```

목적:

- 1,116건을 한 번에 프론트에서 렌더링하지 않음
- 초기 화면 응답량 감소
- 데이터 목록 UX 개선

프론트엔드에서는 페이지 이동 또는 더보기 방식 중 하나를 사용한다.

---

# 31. 콜드스타트 UX

Render 무료 티어의 첫 요청 지연을 고려하여 프론트엔드에서 API 요청 중:

```text
서버를 깨우는 중이에요. 잠시만 기다려 주세요.
```

와 같은 안내 문구를 표시한다.

특히 첫 채팅 요청에서 로딩 상태가 반드시 보이도록 한다.

미션에서도 무료 티어의 첫 요청 지연에 대한 사용자 안내를 요구한다.

---

# 32. 비용 제한

OpenAI API 호출 비용을 고려하여 `/api/chat`에 출력 토큰 제한을 둔다.

예:

```text
max_tokens = 500
```

개발 단계에서는 테스트 질문과 작은 데이터셋으로 먼저 검증한다.

---

# 33. 프론트엔드 요구사항

프레임워크를 사용하지 않는다.

사용 기술:

```text
HTML
CSS
JavaScript
```

## 33-1. 채팅 화면

필수 기능:

- 메시지 입력
- 전송
- 사용자 메시지 표시
- AI 답변 표시
- 로딩 상태
- 오류 상태
- 새 대화 시작

## 33-2. 데이터 관리 화면

필수 기능:

- 거래 목록 확인
- 거래 추가
- 거래 수정
- 거래 삭제

미션상 CRUD 중 최소 1개 동작이 화면에서 확인되어야 하지만, 본 제품에서는 전체 CRUD UX를 구현하는 것을 목표로 한다.

## 33-3. 대화 기록 화면

- 이전 대화 목록
- 대화 선택
- 전체 메시지 불러오기
- 이어서 질문하기

## 33-4. 데이터 요약 화면

다음 정보를 표시한다.

- 데이터 기간
- 거래 건수
- 총 수입
- 총 지출
- 순증감
- 최근 추세

---

# 34. 배포

## Backend

Render

```text
FastAPI
Swagger: /docs
```

배포 후 다음 주소가 접속 가능해야 한다.

```text
https://<backend-domain>/docs
```

## Frontend

Vercel

`frontend/js/config.js`의 `API_BASE_URL`을 Render 배포 URL(https)로 직접 변경한 후
커밋·재배포한다. 빌드 과정 없는 정적 사이트이므로 Vercel 환경변수로 주입하지 않는다.

---

# 35. README 요구사항

README.md에는 최소 다음을 포함한다.

## 서비스 소개

무엇을 해결하는 AI 비서인지 설명.

## 기술 스택

```text
FastAPI
Firebase Firestore
OpenAI API
Vanilla HTML/CSS/JS
Render
Vercel
```

## 배포 URL

- Frontend
- Backend API
- Swagger

## 로컬 실행 방법

백엔드 및 프론트엔드 실행 방법.

## 환경변수 및 프론트 설정값

백엔드 환경변수:

```text
OPENAI_API_KEY
OPENAI_BASE_URL
OPENAI_MODEL
FIREBASE_SERVICE_ACCOUNT_JSON
ALLOWED_ORIGINS
```

프론트 설정값은 `frontend/js/config.js`의 `API_BASE_URL`이며, Render 배포 URL로
직접 변경 후 커밋·재배포하는 방법을 명시한다. 모델명은 AI 연동 구현 시 결정한다.

## 개인정보 처리

원본 거래내역을 저장소에 포함하지 않았음을 명시.

---

# 36. 제출 스크린샷

README에는 최소 다음 화면을 첨부한다.

## 스크린샷 1

데이터 요약이 보이는 채팅 화면.

질문과 AI 답변이 함께 보이도록 한다.

## 스크린샷 2

데이터 관리 화면.

CRUD 중 최소 1개 동작이 실제 수행된 장면.

## 스크린샷 3

대화 기록 화면.

이전 대화를 선택하여 불러온 장면.

스크린샷에는 개인 식별 정보가 노출되지 않아야 한다.

---

# 37. 검증 기준

개발 완료 후 다음 기준으로 검증한다.

## 필수 기능

- [ ] 데이터 1,116건 적재
- [ ] POST `/api/data`
- [ ] GET `/api/data`
- [ ] PUT `/api/data/{id}`
- [ ] DELETE `/api/data/{id}`
- [ ] GET `/api/data/summary`
- [ ] POST `/api/conversations`
- [ ] GET `/api/conversations`
- [ ] GET `/api/conversations/{id}`
- [ ] DELETE `/api/conversations/{id}`
- [ ] POST `/api/chat`
- [ ] Swagger `/docs`
- [ ] Render 배포
- [ ] Vercel 배포

## AI 검증

- [ ] summary가 실제 DB에서 최신 상태로 계산됨
- [ ] 매 `/api/chat` 요청마다 summary를 재조회
- [ ] 시스템 프롬프트에 summary가 주입됨
- [ ] AI가 실제 데이터 숫자를 이용하여 답변
- [ ] 존재하지 않는 데이터를 추측하지 않음
- [ ] 기존 conversation을 이어서 사용할 수 있음
- [ ] chat 이후 대화 내용이 자동 저장됨

## 데이터 검증

- [ ] value 부호 규칙 준수
- [ ] total_income 계산 정확
- [ ] total_expense 계산 정확
- [ ] net 계산 정확
- [ ] trend 계산 정확
- [ ] CRUD 이후 summary 값이 변경됨

## 보안 검증

- [ ] API Key 하드코딩 없음
- [ ] Firebase 서비스 계정 정보 하드코딩 없음
- [ ] `.env` Git 커밋 없음
- [ ] 원본 KB 엑셀 Git 커밋 없음
- [ ] 개인정보가 README/스크린샷에 노출되지 않음

---

# 38. 미션 요구사항 추적표

| 미션 요구사항 | PRD 위치 | 상태 |
|---|---|---|
| 데이터 기반 AI 채팅 | 19~23 | ✅ |
| 데이터 CRUD | 9~12 | ✅ |
| 데이터 summary | 13~14 | ✅ |
| 대화 저장 | 15 | ✅ |
| 대화 목록 | 16 | ✅ |
| 대화 불러오기 | 17 | ✅ |
| 대화 삭제 | 18 | ✅ |
| 컨텍스트 주입 | 20~22 | ✅ |
| Firestore | 6, 8, 28 | ✅ |
| Pydantic 검증 | 25 | ✅ |
| CORS | 26 | ✅ |
| 환경변수 | 27 | ✅ |
| Render | 34 | ✅ |
| Vercel | 34 | ✅ |
| Swagger | 34 | ✅ |
| README | 35 | ✅ |
| 스크린샷 | 36 | ✅ |
| 최소 100개 데이터 | 29 | ✅ |
| Function Calling | 24 | 🟡 보너스 |

---

# 39. 보너스 범위

기본 미션 완료 이후 다음 기능을 선택적으로 구현한다.

1. Function Calling
2. MCP Server 또는 GPT Actions 연동
3. 카테고리별 상세 분석
4. 그래프 시각화
5. CSV/JSON 내보내기
6. 다크 모드

보너스 기능은 기본 기능의 안정성을 해치지 않는 범위에서 진행한다.

---

# 40. PRD 완료 조건

다음 조건을 만족하면 본 PRD의 기본 요구사항이 충족된 것으로 본다.

```text
1,116건 거래 데이터
        ↓
Firestore 저장
        ↓
summary 계산
        ↓
FastAPI
        ↓
AI system prompt에 summary 주입
        ↓
GPT 답변
        ↓
conversation 자동 저장
        ↓
Vanilla JS 프론트에서 조회/관리
        ↓
Render + Vercel 배포
```

본 문서를 기준으로 Task를 작성한다.