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
- **OpenAI 모델**: `gpt-5.5`로 확정(코디세이 프록시가 지원하는 11종 확인 후 결정).
  `OPENAI_MODEL` 환경변수로 주입, 코드에 하드코딩하지 않는다.
- **OpenAI는 직접 호출이 아니라 코디세이 프록시 경유**: 발급받은 키가 `sk-cody-live-`로
  시작하며, `OPENAI_BASE_URL`(`https://copa.codyssey.kr/v1`) 환경변수를 OpenAI 클라이언트의
  `base_url` 파라미터로 반드시 넘겨야 한다. 안 넘기면 기본값인 `api.openai.com`으로
  요청이 나가서 실패한다.
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

- Phase 1(프로젝트 초기 설정): 완료.
- Phase 2(Firestore 연동 + 초기 데이터 적재): 완료. 1,116건(입금254/지출862) 적재 검증됨.
- Phase 3(데이터 API CRUD+summary): 완료.
- Phase 4(Trend 계산): 완료. Phase 3의 summary가 trend를 필요로 해서 같이 구현됨.
- Phase 5(대화 기록 API): 완료.
- Phase 6(AI 챗봇 API): 완료. 모델 `gpt-5.5` 확정.
- Phase 7(Render 배포): 7.1(requirements.txt pip freeze 고정)·7.2(민감정보 커밋 이력
  없음 확인) 완료. 7.3/7.4(Render 대시보드 서비스 생성·환경변수 등록)는 사용자가 직접
  진행 완료(배포 URL: https://my-ai-assistant-bogq.onrender.com). 7.5는 미확인.
- Phase 8(프론트엔드 개발): 전부 완료. `frontend/js/config.js`(API_BASE_URL)·`api.js`
  (fetch 래퍼)를 추가하고 4개 화면(채팅/대화 기록/데이터 요약/거래 내역)을 목업에서
  실제 API 연동으로 교체. `POST /api/conversations`는 채팅 흐름에서 호출하지 않음(자동
  저장과 중복 방지 재확인). 사이드바 D+n 카운터는 `new Date()` 기준 실시간 계산으로
  변경, 콜드스타트 안내 문구는 실측(~43초) 반영해 "최대 1분" 표현으로 조정. 요약 화면의
  월별 막대그래프는 API가 월별 세부 데이터를 안 줘서 제거(trend 배지만 유지, 사용자
  확인 완료). Playwright 헤드리스 브라우저로 4개 화면 실데이터 동작 + CRUD 왕복 +
  콘솔/네트워크 에러 0건 확인.
- Phase 9(프론트엔드 배포 + 통합 검증): 9.1(GitHub push)·9.3(config.js를 Render 실주소로
  변경)·9.5(PRD 37번 32개 항목 배포 URL 기준 재확인)·9.6(README.md + 스크린샷 3종) 완료.
  9.2(Vercel 배포)·9.4(Render ALLOWED_ORIGINS 좁히기)는 사용자가 대시보드에서 직접 진행—
  Vercel 배포 URL: https://my-ai-assistant-weld.vercel.app. 9.5 검증 결과 32개 중 31개
  PASS, 나머지 1개(README/스크린샷 개인정보 미노출)는 9.6 완료 후 재확인해서 PASS로 전환
  — 실패 항목 없음. 사실상 핵심 미션(Phase 1~9) 기능 요구사항 충족.

## 개발 순서

`Task.md`의 Phase 순서(1 → 9)를 그대로 따른다. 한 Phase를 끝내면 다음 Phase로 넘어가기
전에 완료 기준(각 Task 상세 스펙에 적힌 "완료 기준")을 실제로 확인한다.
