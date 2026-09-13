# 프로젝트 작업 지침

먼저 docs/PRD.md와 docs/Task.md를 읽고 실제 코드·git diff와 대조한다.
사용자의 최신 요청이 과거 문서보다 우선한다. 완료 보고는 구현·로컬 검증·배포 검증을
구분한다. 과거 감사 결과는 docs/AUDIT.md이며 현재 상태로 오인하지 않는다.

- 저장소: backend/ FastAPI·Firestore·OpenAI, frontend/ 바닐라 HTML/CSS/JS.
- 선택 보너스: 인사이트·UX 고도화. Function Calling·MCP는 제거했으며 다시 추가하지 않는다.
- summary는 요청당 전체 거래 1회 조회, 같은 데이터로 기본·월별·추가 지표 계산. 캐싱 없음.
- Render Root=backend. Vercel Root=frontend, Other, node build.mjs, Output=dist.
- 프론트 공개 API 주소는 Vercel API_BASE_URL에서 dist/js/config.js로 생성한다.
  로컬 직접 실행에는 frontend/js/config.js 사용. 프론트에 비밀키를 넣지 않는다.
- AI 모델 gpt-5.5 유지. 코디세이 OPENAI_BASE_URL 프록시 사용. 모델·키는 환경변수.
- 채팅은 대화 저장에 성공해야 200. 저장 1회 재시도, 실패 500. 없는 대화는 404.
- 거래를 익명화한다는 이유로 삭제하지 않는다. 원본 엑셀·실제 DB는 별도 요청 없이 변경 금지.
- category null·사용자 정의 값을 임의로 다른 분류로 바꾸지 않는다.
- .env·서비스 계정 키·원본 엑셀·로그를 커밋하지 않는다.
- pytest 등 테스트 프레임워크와 tests/ 폴더는 도입하지 않는다. 작은 로컬 검증으로 확인한다.
- OAuth·낙관적 락 등 과거 거절된 확장을 임의로 추가하지 않는다.
- Phase 10.1~10.7은 로컬 구현·검증, 10.8 실제 재배포 검증은 대기. git 커밋은 아직 없음.
