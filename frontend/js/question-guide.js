// 고정 질문을 고르는 로컬 안내. API·채팅 입력·대화 상태에 접근하지 않는다.
const QuestionGuide = (function () {
  'use strict';

  const interests = [
    {
      label: '내 소비 패턴 이해하기',
      topics: [
        { label: '1년 전체의 특징', question: '내 1년치 거래에서 드러나는 출금 패턴의 특징 3가지를 분석해줘. 실제 기록 기간을 먼저 밝히고, 각 특징에 금액·비율 또는 거래 사례와 앞으로 점검할 부분을 덧붙여줘. 계좌이체를 실제 소비로 단정하지 말고, 관찰한 사실과 추정을 구분해줘.' },
        { label: '소액 출금과 큰 출금의 비중', question: '전체 기록에서 1만원 이하 소액 출금의 건수·금액 비중과 금액이 큰 출금 상위 10건의 금액 비중을 비교해줘. 비율의 기준을 밝히고, 자주 나가는 작은 금액과 몇 건의 큰 금액 중 어느 쪽이 전체 출금 규모에 더 영향을 주는지 설명해줘. 두 집단은 겹칠 수 있으니 비중을 합산하지 말고, 명세가 일부 생략됐다면 소액 출금의 전체 비중은 확정하지 말아줘.' },
        { label: '같은 내용으로 반복되는 출금', question: '기록된 거래 내용과 분류가 같은 반복 출금 중 점검할 만한 항목을 최대 3개 골라줘. 각 항목의 횟수·합계·발생한 월을 근거로 반복 양상을 설명하고, 구독이나 고정비인지 판단하려면 무엇을 확인해야 하는지 알려줘. 반복된다는 이유만으로 정기 결제로 확정하거나 기록에 없는 상대방·소비 목적을 만들어내지 말아줘.' },
      ],
    },
    {
      label: '변화의 원인 살펴보기',
      topics: [
        { label: '출금이 늘어난 시기의 특징', question: '월별 기록에서 전월보다 출금이 늘어난 시기를 최대 2곳 찾아, 증가액과 증가율을 근거로 그 시기의 특징을 설명해줘. 큰 출금이나 반복 거래가 증가와 어떻게 관련되는지 살펴보되, 기록으로 확인되는 변화와 원인에 대한 추정을 구분해줘. 첫 달과 마지막 달이 일부 기간일 수 있음을 고려하고, 비교 기준이 0원이면 증가율 대신 금액 차이로 설명해줘. 증가한 시기가 없다면 없다고 알려줘.' },
        { label: '월별 출금 차이를 만든 거래', question: '기록 범위를 확인해 비교하기에 적절한 연속된 두 달을 고르고, 두 달의 출금 차이를 설명하는 데 도움이 되는 거래 사례를 최대 3개 찾아줘. 비교한 연월과 선택 이유, 출금 총액의 차이, 사례별 날짜·기록된 내용·금액을 제시해줘. 큰 거래만으로 월 전체 차이를 모두 설명했다고 단정하지 말고, 확인하지 못한 나머지 차이는 구분해줘.' },
        { label: '최근 기록과 이전 기록 비교하기', question: '데이터의 최신 거래월을 기준으로 최근 3개월과 그 이전 3개월의 출금 패턴을 비교해줘. 두 구간의 실제 연월과 월평균 출금액·차이·변화율을 밝히고, 거래 사례를 근거로 달라진 점을 설명해줘. 첫 달과 마지막 달의 기록 범위 차이를 고려하고, 비교할 자료가 부족하면 단정 대신 추가로 확인할 사항을 알려줘.' },
      ],
    },
    {
      label: '앞으로의 관리 방향 정하기',
      topics: [
        { label: '먼저 점검할 항목', question: '내 거래 기록에서 앞으로 먼저 점검할 항목 3개를 우선순위로 정해줘. 큰 출금의 집중도, 같은 내용의 반복, 월별 변화 중 실제 근거가 있는 것을 활용해 각 항목의 금액·비율 또는 사례와 먼저 확인할 질문을 알려줘. 계좌이체와 미분류 거래는 목적 확인이 필요한 항목으로 다루고, 바로 줄여야 할 소비라고 단정하지 말아줘.' },
        { label: '다음 달 예산을 세우는 기준', question: '데이터의 최신 거래월 다음 달을 위한 예산 초안을 세우는 기준을 제안해줘. 기준이 되는 실제 연월을 밝히고, 기록 범위를 고려해 비교 가능한 월들의 입출금 수치로 출발점을 설명해줘. 계좌이체를 생활비로 포함하거나 기록에 없는 소비 분류를 만들지 말고, 목적 확인이 필요한 금액은 따로 구분해줘. 예산 금액은 미래 수입을 보장하지 않는 가정·제안으로 제시하고, 자료가 부족하면 먼저 확인할 정보를 알려줘.' },
        { label: '실천할 관리 방법 3가지', question: '내 거래에서 확인되는 패턴을 근거로 앞으로 실천할 관리 방법 3가지를 제안해줘. 각 방법에 실제 수치나 거래 사례, 내가 할 행동, 한 달 뒤 확인할 지표를 하나씩 연결해줘. 반복 출금을 무조건 해지하라고 권하지 말고, 감축 금액이나 목표 비율을 제시한다면 가정임을 밝혀줘. 기록만으로 알 수 없는 소비 목적은 먼저 확인하도록 안내해줘.' },
      ],
    },
  ];

  const byId = id => document.getElementById(id);
  const launcher = byId('guideLauncher');
  const panel = byId('questionGuidePanel');
  const title = byId('guideTitle');
  const path = byId('guidePath');
  const intro = byId('guideIntro');
  const choices = byId('guideChoices');
  const question = byId('guideQuestion');
  const resultActions = byId('guideResultActions');
  const status = byId('guideStatus');
  const copyButton = byId('guideCopy');
  const back = byId('guideBack');
  const reset = byId('guideReset');
  let interestIndex = null;
  let topicIndex = null;
  let copyRevision = 0;
  let positionFrame = 0;

  // 패널은 상단 로봇을 따라 배치하고 화면 밖으로 넘치지 않게 한다.
  function positionPanel() {
    if (panel.hidden) return;
    const viewport = window.visualViewport;
    const leftEdge = viewport?.offsetLeft || 0;
    const topEdge = viewport?.offsetTop || 0;
    const width = viewport?.width || document.documentElement.clientWidth;
    const height = viewport?.height || window.innerHeight;
    const anchor = launcher.getBoundingClientRect();
    if (anchor.bottom < topEdge || anchor.top > topEdge + height) { close(false); return; }
    const gap = 12;
    const panelWidth = Math.min(360, width - gap * 2);
    panel.style.width = panelWidth + 'px';
    panel.style.left = Math.max(leftEdge + gap, Math.min(anchor.right - panelWidth, leftEdge + width - panelWidth - gap)) + 'px';
    // 작은/가로 화면에서는 위로 당겨 읽을 공간을 확보한다. 닫기와 복사는 항상 보인다.
    const readingHeight = Math.min(520, height - gap * 2);
    const top = Math.max(topEdge + gap, Math.min(anchor.bottom + 10, topEdge + height - readingHeight - gap));
    panel.style.top = top + 'px';
    panel.style.maxHeight = Math.max(120, topEdge + height - top - gap) + 'px';
  }

  function schedulePosition() {
    if (panel.hidden || positionFrame) return;
    positionFrame = requestAnimationFrame(() => { positionFrame = 0; positionPanel(); });
  }

  function clearCopyStatus() {
    copyRevision += 1;
    copyButton.disabled = false;
    status.textContent = '';
  }

  function render(focus = true) {
    clearCopyStatus();
    const interest = interests[interestIndex];
    const topic = interest?.topics[topicIndex];
    path.hidden = !interest;
    path.textContent = interest ? interest.label + (topic ? ' › ' + topic.label : '') : '';
    title.textContent = topic ? '추천 질문' : interest ? '세부 관심사 선택' : '질문 추천받기';
    intro.textContent = topic
      ? '이 질문을 추천해요. 복사해서 AI 채팅 입력창에 붙여 넣어 보세요.'
      : interest ? '어떤 내용을 더 살펴보고 싶으세요?'
        : '어떤 점이 궁금하세요? 관심사를 고르면 AI에게 물어볼 질문을 추천해 드릴게요.';
    question.hidden = !topic;
    question.textContent = topic?.question || '';
    resultActions.hidden = !topic;
    choices.hidden = !!topic;
    choices.replaceChildren();
    if (!topic) {
      (interest ? interest.topics : interests).forEach((item, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'guide-choice';
        button.textContent = item.label;
        button.addEventListener('click', () => {
          if (interestIndex === null) interestIndex = index;
          else topicIndex = index;
          render();
        });
        choices.appendChild(button);
      });
    }
    back.disabled = interestIndex === null;
    reset.disabled = interestIndex === null;
    byId('guideBody').scrollTop = 0;
    panel.scrollTop = 0;
    positionPanel();
    if (focus) title.focus({ preventScroll: true });
  }

  function close(restoreFocus = true) {
    if (panel.hidden) return;
    panel.hidden = true;
    launcher.setAttribute('aria-expanded', 'false');
    clearCopyStatus();
    if (restoreFocus) launcher.focus({ preventScroll: true });
  }

  launcher.addEventListener('click', () => {
    if (!panel.hidden) { close(); return; }
    panel.hidden = false;
    launcher.setAttribute('aria-expanded', 'true');
    render();
  });
  byId('guideClose').addEventListener('click', () => close());
  back.addEventListener('click', () => {
    if (topicIndex !== null) topicIndex = null;
    else interestIndex = null;
    render();
  });
  reset.addEventListener('click', () => {
    interestIndex = null;
    topicIndex = null;
    render();
  });
  byId('guideExplore').addEventListener('click', () => { topicIndex = null; render(); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) {
      event.preventDefault();
      close();
    }
  });
  // 바깥 기능을 선택하면 그 조작을 막거나 포커스를 빼앗지 않고 패널만 닫는다.
  document.addEventListener('click', event => {
    // 단계 변경으로 클릭한 버튼이 제거되어도 원래 이벤트 경로는 유지된다.
    const origin = event.composedPath();
    if (!panel.hidden && !origin.includes(panel) && !origin.includes(launcher)) close(false);
  });
  copyButton.addEventListener('click', async () => {
    const text = interests[interestIndex]?.topics[topicIndex]?.question;
    if (!text || copyButton.disabled) return;
    const revision = ++copyRevision;
    copyButton.disabled = true;
    status.textContent = '';
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(text);
      if (revision === copyRevision && !panel.hidden) status.textContent = '질문을 복사했어요';
    } catch {
      if (revision === copyRevision && !panel.hidden) {
        status.textContent = '자동 복사가 되지 않았어요. 질문 본문을 직접 선택해 복사해 주세요.';
        question.focus({ preventScroll: true });
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(question);
        selection?.removeAllRanges();
        selection?.addRange(range);
      }
    } finally {
      if (revision === copyRevision) copyButton.disabled = false;
    }
  });
  window.addEventListener('resize', schedulePosition);
  window.addEventListener('scroll', schedulePosition, true);
  window.visualViewport?.addEventListener('resize', schedulePosition);
  window.visualViewport?.addEventListener('scroll', schedulePosition);
  // 첫 summary 요청의 대기 안내나 제목 줄바꿈으로 상단 높이가 달라질 수 있다.
  const headerObserver = new ResizeObserver(schedulePosition);
  headerObserver.observe(document.querySelector('#view-chat > .view-header'));
  headerObserver.observe(byId('coldstartNote'));
  render(false);
  return { close };
})();
