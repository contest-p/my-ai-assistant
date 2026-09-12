# CLAUDE.md

이 프로젝트에서 작업할 때는 아래를 먼저 확인하세요.

## 문서 (docs/)
- `docs/PRD.md` — API 스펙, 데이터 스키마, 계산 규칙의 최종 확정본. 구현은 반드시 이 문서 기준.
- `docs/Task.md` — 상단 체크리스트(진행 상황) + 하단 상세 스펙(Phase.Task 번호로 연결).
- `docs/기술스택.md` — 기술 스택 확정 사항과 이유.
- `docs/시나리오.md` — 왜 이렇게 설계했는지의 배경.

작업 시작 전에 `Task.md` 상단 체크리스트를 보고 지금 어느 Phase.Task인지 확인하고,
해당 번호의 "상세 스펙" 섹션을 읽고 시작하세요. 애매한 부분이 있으면 진행하기 전에
먼저 물어보세요 — 임의로 판단해서 진행하지 마세요.

## 절대 잊으면 안 되는 것 (여러 차례 검토를 거쳐 확정된 것들)

- **저장소 구조**: 단일 repo, `backend/` + `frontend/` 분리. Render Root Directory=`backend`,
  Vercel Root Directory=`frontend`.
- **프론트 API 주소**: `frontend/js/config.js`의 `API_BASE_URL`을 배포 직전에 직접 수정해서
  커밋한다. Vercel 환경변수로 넣지 않는다 — 빌드 과정이 없는 바닐라 JS라 반영이 안 된다.
- **OpenAI 모델명**: 아직 미정. `OPENAI_MODEL` 환경변수로 주입하고, 코드에 특정 모델명을
  하드코딩하지 않는다.
- **OpenAI는 직접 호출이 아니라 코디세이 프록시 경유**: 발급받은 키가 `sk-cody-live-`로
  시작하며, `OPENAI_BASE_URL`(`https://copa.codyssey.kr/v1`) 환경변수를 OpenAI 클라이언트의
  `base_url` 파라미터로 반드시 넘겨야 한다. 안 넘기면 기본값인 `api.openai.com`으로
  요청이 나가서 실패한다. 이 프록시가 지원하는 모델 목록도 일반 OpenAI와 다를 수
  있으니 Phase 6에서 직접 확인 후 `OPENAI_MODEL`을 정한다.
- **category 미매핑**: 값이 없으면 항상 `null`. value 부호로 추측해서 채우지 않는다.
- **summary 계산**: `GET /api/data/summary`는 `data` 컬렉션 전체를 매번 다시 읽어서
  계산한다(페이지네이션된 목록 재사용 금지). 이 계산 로직(`analysis_service.get_summary()`)은
  `POST /api/chat`에서도 그대로 재사용한다 — 같은 로직을 두 곳에 따로 구현하지 않는다.
- **채팅 자동저장**: `/api/chat`은 대화 저장에 성공해야 200을 반환한다. 저장 실패 시 1회
  재시도, 그래도 실패하면 500(AI 답변을 버리고).
- **conversation_id 404**: 존재하지 않는 `conversation_id`가 오면 조용히 새 대화를 만들지
  말고 404를 반환한다.
- **테스트**: pytest 같은 자동 테스트 프레임워크는 이 프로젝트 범위 밖이다. Swagger UI
  수동 확인으로 충분하다. `tests/` 폴더를 만들지 않는다.
- **커밋 금지 목록**: 원본 KB 엑셀, Firebase 서비스 계정 JSON, `.env` — 전부 `.gitignore`에
  이미 걸려 있음. 실수로 추가하지 않는다.
- **보너스(Function Calling)**: Phase 1~9가 배포까지 다 끝나기 전엔 건드리지 않는다.
  별도 사이클로 진행한다.

## 진행 상황

- Phase 1(프로젝트 초기 설정): 전부 완료 (1.1~1.7).
- Phase 2(Firestore 연동 + 초기 데이터 적재): 전부 완료. `config.py`에서 firebase-admin
  초기화, `scripts/import_data.py`로 1,116건 적재 및 검증 완료(입금 254 / 지출 862,
  category 미매핑 0건). 마스킹된 거래상대방("***", "토스 ***")의 memo는 입출금 방향
  기준으로 "계좌이체 송금"/"계좌이체 입금"으로 일반화하기로 확정(사용자 확인 완료).
- Phase 3(데이터 API CRUD + Summary): 전부 완료. `routers/data.py`에 5개 엔드포인트
  (POST/GET/PUT/DELETE `/api/data`, GET `/api/data/summary`) 구현, curl로 정상 케이스와
  404 케이스 모두 확인.
- Phase 4(Trend 계산): 전부 완료. `get_summary()`가 trend 없이는 동작할 수 없어 Phase 3
  작업 중 `analysis_service.calculate_trend()`를 함께 구현했고, 실제 데이터로 "+40%
  증가" 결과를 확인해 PRD/Task 4.5 검산값과 일치함을 검증했다.
- Phase 5(대화 기록 API): 전부 완료. `routers/conversations.py`에 4개 엔드포인트
  (POST/GET/GET-by-id/DELETE `/api/conversations`) 구현, curl로 저장→목록→불러오기→삭제→
  404 순서 그대로 검증. `POST /api/conversations`는 `/api/chat`(Phase 6)의 자동저장과
  별개 엔드포인트라는 것을 계속 의식할 것 — Phase 8 프론트 연동 시 일반 채팅 흐름에서
  이 엔드포인트를 중복 호출하지 않도록 주의.
- Phase 6부터는 아직 시작 전.

## 개발 순서

`Task.md`의 Phase 순서(1 → 9)를 그대로 따른다. 한 Phase를 끝내면 다음 Phase로 넘어가기
전에 완료 기준(각 Task 상세 스펙에 적힌 "완료 기준")을 실제로 확인한다.
