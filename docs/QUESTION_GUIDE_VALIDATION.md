# 선택형 질문 추천 안내 — 2026-10-04

## 범위와 구현

사용자가 설계를 확인한 뒤 “수정해줘”로 구현을 승인했다. 시작 HEAD는 `f54dab9`이며
작업 트리는 깨끗했다. 이번 변경은 프론트엔드·정적 이미지·문서에 한정한다.

- `frontend/js/question-guide.js`: 고정 관심사 3개와 질문 9개, 선택·복사·키보드 처리.
  `Api`, `fetch`, Firestore, AI, 채팅 입력값·대화 ID에 접근하지 않는다.
- 로봇은 `#btnNewChat` 바로 왼쪽의 실제 button 한 개. 56px(모바일 48px), 이름은
  “질문 추천받기”. 이미지의 빈 alt는 버튼 이름과 중복 낭독하지 않기 위한 처리다.
- 질문은 `textContent`로 표시한다. 입력창·자동 전송·자동 붙여넣기 없음.
- 닫았다 열면 선택을 유지한다. 다른 화면으로 이동하면 닫고 선택을 유지한다.
  새로고침 시 초기화하며 DB·localStorage에 안내 상태를 저장하지 않는다.
- 이전: 결과→세부 선택→관심사 선택. 다른 질문 찾아보기: 현재 관심사의 세부 선택.
  처음부터: 관심사·세부 선택을 모두 초기화한다.
- 비모달 패널: 열기/단계 변경 후 제목 포커스, Tab으로 선택 가능, Escape/닫기로
  로봇 포커스 복귀. 바깥 버튼 조작·화면 전환은 해당 조작의 포커스를 빼앗지 않는다.
- 데스크톱에서 로봇 아래 근처에 펼치며 좁거나 낮은 화면에서는 위로 조정한다.
  본문은 내부 스크롤, 닫기·복사·이전·처음부터는 별도 영역에 유지한다.
  스크롤로 로봇이 화면 밖으로 나가면 안내를 닫고 선택은 보존한다.
- 클립보드 쓰기 완료 후에만 성공 표시. 거부·미지원 시 실패 안내와 본문 선택을 제공한다.
  이전 질문의 비동기 복사 완료가 현재 질문에 성공 메시지를 표시하지 않도록 구분한다.
- 기존 빠른 조회/채팅/삭제 로직은 유지한다. `app.js`에는 화면 전환 시 닫기 연결만 추가.
- 정적 빌드가 `assets/`도 `dist/assets/`로 복사한다. 공개 API 주소 생성 계약 유지.

## 로컬 검증

운영 주소에 접속하지 않는 Chrome 헤드리스 브라우저와 합성 응답 서버로 검증했다.
외부 요청은 차단/대체했다. 서버는 127.0.0.1만 사용했고 실제 거래나 대화는 읽거나
수정하지 않았다. 검증 보조 파일·스크린샷은 git에서 제외된 `.local-validation/`에 둔다.
pytest, tests 폴더, 제품용 외부 라이브러리는 추가하지 않았다.

| 검증 | 결과 |
| --- | --- |
| 관심사 3 × 세부 선택 3 | 서로 다른 질문 9개, 선택 경로와 문구 확인 |
| 이전·처음부터·다른 질문·닫기·재열기 | 정상, 복사 상태 초기화 및 선택 보존 |
| 클립보드 | 실제 쓰기/읽기 일치, 거부·미지원 실패 안내 및 본문 선택 |
| 늦게 완료되는 복사 | 단계 변경 후 이전 요청의 성공 안내가 나오지 않음 |
| 추가 API 요청 | 앱 초기 summary 1회와 분리하여 안내 경로 반복 중 0회 |
| 작성 중 입력·대화 | 안내 전후 입력 보존, 메시지 보존, 후속 전송의 conversation_id 유지 |
| 빠른 조회 | 4종 요청 및 결과, AI 채팅 요청 0회 |
| 기존 채팅·새 대화·삭제 | 가짜 API로 전송·후속 질문·삭제 및 새 conversation_id=null 확인 |
| 키보드 | Enter/Space 열기·선택, Tab으로 패널 밖 이동 가능, Escape 및 닫기 후 로봇 포커스 |
| 화면 | 1440×1000, 1024×768, 720×900, 390×844, 320×568, 844×390의 양 테마 |
| 배치 | 로봇/테마/새 대화 겹침 없음, 가로 넘침 없음, 패널과 조작 버튼이 뷰포트 안에 위치 |
| 본문·스크롤 | 긴 질문 끝까지 내부 스크롤, 상단 로봇이 화면 밖으로 나가면 닫기, 재열기 유지 |
| 이미지 | 224×224 PNG, RGBA 투명도, 약 96KB, dist 복사 확인 |
| 정적 검사 | JS 구문, 정적 빌드, git diff --check 통과, 브라우저 JS 오류 0건 |

빌드 검증은 `frontend/`에서 검증용 `API_BASE_URL=http://127.0.0.1:4319`를 설정하고
`node build.mjs`로 실행했다. 기존 `frontend/js/config.js`는 변경하지 않았다.
검증용 `dist/`는 git 제외 대상이며 실제 배포 시 Vercel 환경변수로 다시 생성해야 한다.

재확인 시 위 크기·테마에서 첫 화면과 긴 질문을 열고, 내부 스크롤 및 복사 버튼 접근,
입력 보존·선택 유지·Escape를 확인한다. 네트워크 기록은 첫 summary 응답 이후부터
안내만 조작한 구간을 분리하여 확인한다. 실제 채팅 전송은 분석·대화 저장을 발생시키므로
이번 로컬 검증에서는 가짜 서버로 대체했다.

## 이미지 제작 기록

내장 image_gen으로 생성했으며 CLI/API 키 기반 생성은 사용하지 않았다.
원본 alpha를 유지하며 웹용으로 224×224 PNG로 축소했다.
제품 자산: `frontend/assets/question-guide-robot.png`.

사용한 생성 프롬프트:

> Create one polished 3D raster mascot asset for a Korean personal finance question-guide button, transparent alpha background, square composition, no text. Cute small rounded pearl white robot, large round head and a very small rounded torso. Deep navy/black glossy face screen, two large bright soft white/cyan glowing oval eyes, subtle teal blue violet rim around face. Friendly soft dimensional studio shading. It wears a recognizable Republic of Korea Marine Corps eight-point utility cover (대한민국 해병대 팔각모): low angular crown, distinctly faceted eight-point/octagonal top perimeter, flat top visible in slightly elevated frontal view, short broad visor, muted olive/khaki fabric with very subtle simplified camouflage if needed. NOT a baseball cap with a domed crown, NOT a beret, NOT a helmet. Hat fits naturally on head and does not hide either eye. No writing, no tiny badge detail, no weapons. Prioritize the eight-point hat silhouette and both eyes at 48–64px displayed size. Robot fills about 90% of square, centered, leave enough transparent padding for hat, all parts visible. Gentle grey contour shading on white shell plus soft edge highlights to remain clear on cream and dark navy site backgrounds. No rectangular backdrop, no checkerboard baked in, no floor, no floor shadow. Maintain the feel of a smooth white spherical companion robot with illuminated colorful face rim, rather than a flat illustration.

## 미검증 및 배포 상태

실제 DB·코디세이 AI 답변 품질·Render/Vercel 배포는 검증하지 않았다.
질문 추천은 정적 안내이며 실제 분석의 정확성을 보장하는 기능이 아니다.
명세 생략·자료 부족은 기존 AI 근거 규칙과 질문의 확인 조건으로 처리한다.
백엔드·모델·캐시·분류·원본 엑셀·운영 DB 변경 없음. 커밋·푸시·배포 미실행.
