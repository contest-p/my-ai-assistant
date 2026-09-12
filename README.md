# 전역 후 1년, 내 소비를 아는 AI 비서

2025.08.18 ~ 2026.08.18의 KB국민은행 거래내역(비식별화)을 기반으로, 사용자의 소비·저축
패턴을 분석하고 자연어로 답변하는 개인 재정 AI 비서입니다. 전역 후 사회 복귀를 준비하는
사용자가 지난 1년간 흩어져 있던 금융 거래를 한눈에 확인하고, AI에게 "이번 달 지출이
평소보다 많은 편이야?" 같은 질문을 자연어로 던져 수입·지출·추세를 이해할 수 있도록
돕습니다.

## 주요 기능

- **데이터 기반 AI 채팅**: 실시간으로 계산한 데이터 요약을 시스템 프롬프트에 주입해,
  실제 숫자에 근거한 답변을 생성합니다. 데이터에 없는 내용은 추측하지 않습니다.
- **거래 데이터 CRUD**: 거래 추가·조회·수정·삭제.
- **데이터 요약**: 총 수입/지출/순증감, 평균, 최대·최소 거래, 이번 달 실적, 최근 3개월
  지출 추세.
- **대화 기록**: 채팅 시 자동 저장되며, 목록에서 불러와 이어서 질문할 수 있습니다.

## 기술 스택

| 영역 | 기술 |
|---|---|
| 백엔드 | FastAPI |
| 데이터베이스 | Firebase Firestore |
| AI | OpenAI API (코디세이 프록시 경유, 모델: `gpt-5.5`) |
| 프론트엔드 | Vanilla HTML / CSS / JavaScript (빌드 과정 없음) |
| 백엔드 배포 | Render |
| 프론트엔드 배포 | Vercel |

## 배포 URL

- **Frontend**: https://my-ai-assistant-weld.vercel.app
- **Backend API**: https://my-ai-assistant-bogq.onrender.com
- **Swagger**: https://my-ai-assistant-bogq.onrender.com/docs

> Render 무료 티어를 사용하고 있어, 일정 시간 요청이 없으면 서버가 잠들어 있다가 첫
> 요청 시 다시 깨어납니다. 이때 응답까지 최대 1분 정도 걸릴 수 있습니다(프론트엔드에도
> 관련 안내 문구가 표시됩니다).

## 로컬 실행 방법

### 백엔드

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# backend/.env 파일을 만들고 아래 "환경변수" 항목의 5개 값을 채운다
uvicorn main:app --reload
```

`http://localhost:8000/docs`에서 Swagger UI로 API를 확인할 수 있습니다.

### 프론트엔드

빌드 과정이 없으므로, `frontend/` 폴더를 정적 파일 서버로 열기만 하면 됩니다.

```bash
cd frontend
python -m http.server 5500
```

`http://localhost:5500`으로 접속합니다. 로컬 백엔드와 연동하려면
`frontend/js/config.js`의 `API_BASE_URL`을 `http://localhost:8000`으로 바꿔야 합니다
(현재는 배포된 Render 주소로 설정되어 있습니다).

## 환경변수 및 프론트 설정값

백엔드(Render 대시보드 또는 로컬 `backend/.env`)에 다음 5개 환경변수가 필요합니다.

| 변수명 | 설명 |
|---|---|
| `OPENAI_API_KEY` | 코디세이 프록시에서 발급받은 API 키 (`sk-cody-live-`로 시작) |
| `OPENAI_BASE_URL` | 코디세이 프록시 엔드포인트 (`https://copa.codyssey.kr/v1`) — OpenAI 클라이언트의 `base_url`로 반드시 전달해야 함 |
| `OPENAI_MODEL` | 사용할 모델명 (`gpt-5.5`) |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase 서비스 계정 키 JSON의 **내용**을 한 줄 문자열로 담은 값 (파일 경로 아님) |
| `ALLOWED_ORIGINS` | CORS 허용 도메인 (배포 시 Vercel 프론트 도메인으로 제한) |

프론트엔드는 백엔드 환경변수와 별개로 `frontend/js/config.js`의 `API_BASE_URL` 값을
직접 수정한 뒤 커밋·재배포해서 사용합니다. 빌드 과정이 없는 바닐라 JS 정적 사이트라
Vercel 환경변수로는 이 값이 반영되지 않기 때문입니다.

## 개인정보 처리

- 원본 KB국민은행 거래내역 엑셀 파일과 Firebase 서비스 계정 키(JSON)는 이 저장소에
  포함되어 있지 않습니다(`.gitignore` 처리).
- 애플리케이션과 아래 스크린샷에는 비식별화된 파생 데이터만 사용했으며, 거래 상대방의
  실명이 드러나는 값은 일반화된 문구(예: "계좌이체 송금")로 치환했습니다.

## 스크린샷

**1. AI 채팅** — 질문과 실제 데이터에 근거한 AI 답변이 함께 보이는 화면

![채팅 화면](docs/screenshots/01_chat.png)

**2. 데이터 관리** — 거래 추가가 실제로 반영된 화면

![데이터 관리 화면](docs/screenshots/02_data_management.png)

**3. 대화 기록** — 저장된 대화를 목록에서 선택해 불러온 화면

![대화 기록 화면](docs/screenshots/03_conversation_history.png)
