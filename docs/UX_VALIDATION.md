# UX 보너스 로컬 검증 — 2026-09-13

기준: 미션 소개의 인사이트·UX 고도화, PRD 24번. 변경은 미커밋·미배포.
실제 backend 라우트·분석 함수·프론트 파일을 사용하되 Firestore 서비스와 AI 응답만
메모리 내 예제로 대체했다. 실제 DB 쓰기·AI 과금 없음. pytest·tests/ 파일 추가 없음.

| 확인 항목 | 결과 |
|---|---|
| summary 요청당 전체 읽기 1회, 월별 합계와 기본 합계 일치 | PASS |
| 순저축률·최대 지출 월, 빈 데이터·수입 0·중간 빈 월 | PASS |
| POST/GET/PUT/DELETE, 수정 후 최신월 변경, 없는 ID 404 | PASS |
| 실제 존재하지 않는 날짜·공백 memo·필수 필드 null 거부 | PASS |
| CSV/JSON 전체·6개월·3개월 거래 수, BOM·수식 방지·잘못된 format | PASS |
| 기본 컨텍스트 주입·채팅 자동저장·대화 재사용·불러오기·삭제 | PASS (AI는 가짜 응답) |
| 빈 length 응답 1200→2400 한 번 재시도, fallback | PASS |
| /mcp 경로 제거, OpenAI 호출에 tools 없음 | PASS |
| 실제 브라우저 그래프·월별 표·3개월 선택·다운로드 두 형식 | PASS |
| 다크 모드·새로고침 후 유지, 모바일 390px 가로 넘침 없음 | PASS |
| 브라우저 거래 추가/수정/삭제, 미분류 보존, 채팅·대화 불러오기 | PASS |
| 오류·빈 데이터 화면과 다운로드 비활성화 | PASS |
| 브라우저 JavaScript 오류 | 0건 |
| Node 설정 생성: 누락·비정상 URL 거부, 로컬·Render 주소 산출 | PASS |
| Python 구문·JavaScript 구문·git diff 공백 검사 | PASS |

브라우저 캡처는 docs/screenshots/bonus_local_light.png, bonus_local_dark.png,
bonus_local_mobile.png이며 합성 데이터 화면이다. 육안으로 밝은 테마·어두운 테마와
모바일을 확인했다. 임시 검증 스크립트는 저장소 밖 TEMP에 두고 실제 서비스에는 포함하지 않았다.

남음: 실제 Firestore CRUD·코디세이 답변, Render 재배포, Vercel API_BASE_URL 설정 및
재배포, 실제 배포 주소에서 새 버전의 통합 검증·제출 스크린샷 재촬영. 기존 공개 API의
사용자 인증 미구현은 README의 운영 범위에 명시했다.
