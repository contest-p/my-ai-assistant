// ============================================================
// 실제 API(config.js의 API_BASE_URL)와 연동하는 화면 로직 (Phase 8)
// ============================================================

(function () {
  'use strict';

  const DISCHARGE_DATE = new Date(2025, 7, 18); // 2025-08-18 (월은 0-indexed)
  const CATEGORY_OPTIONS = ['카드결제', '계좌이체', '현금인출', '급여', '이자', '기타입금'];
  const PAGE_SIZE = 20;

  /* ---------- 유틸 ---------- */

  function pad2(n) {
    return String(n).padStart(2, '0');
  }

  function todayISO() {
    const d = new Date();
    return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
  }

  function won(n) {
    if (n === null || n === undefined || Number.isNaN(n)) return '—';
    const rounded = Math.round(n);
    const sign = rounded < 0 ? '−' : rounded > 0 ? '+' : '';
    return sign + Math.abs(rounded).toLocaleString() + '원';
  }

  function wonPlain(n) {
    if (n === null || n === undefined || Number.isNaN(n)) return '—';
    return Math.round(n).toLocaleString() + '원';
  }

  function fmtDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return `${d.getFullYear()}.${pad2(d.getMonth() + 1)}.${pad2(d.getDate())}`;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str === null || str === undefined ? '' : String(str);
    return div.innerHTML;
  }

  let toastTimer;
  function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
  }

  /* ---------- 0. 사이드바 D+n 카운터 (실시간 계산, PRD 요구사항 추가 반영) ---------- */

  function updateDayCounter() {
    const now = new Date();
    const todayMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffDays = Math.floor((todayMidnight - DISCHARGE_DATE) / 86400000);
    document.getElementById('dayCounter').textContent = 'D+' + diffDays;
    document.getElementById('sinceDate').textContent =
      `오늘 ${now.getFullYear()}.${pad2(now.getMonth() + 1)}.${pad2(now.getDate())} 기준`;
  }

  updateDayCounter();
  setInterval(updateDayCounter, 60 * 1000); // 자정을 넘기면 페이지를 새로고침하지 않아도 갱신되게

  /* ---------- 1. 콜드스타트 안내 (API 요청 시작~종료에 맞춰 표시, PRD 31) ---------- */

  const coldstartNote = document.getElementById('coldstartNote');
  Api.setRequestHooks({
    onStart: () => coldstartNote.classList.add('show'),
    onEnd: () => coldstartNote.classList.remove('show'),
  });

  /* ---------- 2. 사이드바 / 모바일 탭 전환 ---------- */

  const navButtons = document.querySelectorAll('.nav-item, .mobile-topbar button');
  const views = document.querySelectorAll('.view');

  function switchView(viewName) {
    views.forEach((v) => v.classList.toggle('active', v.id === 'view-' + viewName));
    navButtons.forEach((b) => b.classList.toggle('active', b.dataset.view === viewName));
    if (viewName === 'summary') loadSummary();
    if (viewName === 'data') loadDataPage(0);
    if (viewName === 'history') loadConversations();
  }

  navButtons.forEach((btn) => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });

  /* ---------- 3. 채팅 (8.3) ---------- */

  const chatLog = document.getElementById('chatLog');
  const chatInput = document.getElementById('chatInput');
  const btnSend = document.getElementById('btnSend');
  const typingMsg = document.getElementById('typingMsg');
  let conversationId = null;
  let chatPending = false;

  function appendMessage(role, html, isError) {
    const wrap = document.createElement('div');
    wrap.className = 'msg ' + role;
    wrap.innerHTML = '<div class="bubble' + (isError ? ' error-bubble' : '') + '">' + html + '</div>';
    chatLog.insertBefore(wrap, typingMsg);
    chatLog.scrollTop = chatLog.scrollHeight;
    return wrap;
  }

  function clearChat() {
    chatLog.querySelectorAll('.msg').forEach((el) => {
      if (el !== typingMsg) el.remove();
    });
  }

  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || chatPending) return;
    chatPending = true;
    document.getElementById("btnNewChat").disabled = true;
    appendMessage('user', escapeHtml(text));
    chatInput.value = '';
    btnSend.disabled = true;
    typingMsg.style.display = 'flex';
    chatLog.scrollTop = chatLog.scrollHeight;

    try {
      const res = await Api.postJSON('/api/chat', { message: text, conversation_id: conversationId });
      conversationId = res.conversation_id;
      appendMessage('ai', escapeHtml(res.reply).replace(/\n/g, '<br>'));
    } catch (err) {
      if (err instanceof Api.ApiError && err.status === 404) {
        // 이어서 질문하기로 불러온 대화가 그 사이 삭제된 경우 등 — 다음 질문부터는 새 대화로 이어간다.
        conversationId = null;
      }
      appendMessage('ai', escapeHtml(err.message), true);
    } finally {
      typingMsg.style.display = 'none';
      btnSend.disabled = false;
      chatPending = false;
      document.getElementById("btnNewChat").disabled = false;
      chatLog.scrollTop = chatLog.scrollHeight;
    }
  }

  btnSend.addEventListener('click', sendMessage);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); sendMessage(); }
  });

  document.getElementById('btnNewChat').addEventListener('click', () => {
    conversationId = null;
    clearChat();
  });

  function openConversationInChat(conversation) {
    if (chatPending) { showToast("답변이 끝난 뒤 대화를 바꿔 주세요."); return; }
    conversationId = conversation.id;
    clearChat();
    (conversation.messages || []).forEach((m) => {
      appendMessage(m.role === 'user' ? 'user' : 'ai', escapeHtml(m.content).replace(/\n/g, '<br>'));
    });
    switchView('chat');
  }

  /* ---------- 4. 대화 기록 (8.5) ---------- */

  const convoList = document.getElementById('convoList');

  async function loadConversations() {
    convoList.innerHTML = '<p class="sub">불러오는 중…</p>';
    try {
      const res = await Api.getJSON('/api/conversations');
      if (!res.items.length) {
        convoList.innerHTML = '<p class="sub">아직 저장된 대화가 없어요. AI 채팅에서 질문을 하면 자동으로 저장돼요.</p>';
        return;
      }
      convoList.innerHTML = '';
      res.items.forEach((item) => convoList.appendChild(renderConvoCard(item)));
      if (res.has_more) {
        const notice = document.createElement('p');
        notice.className = 'sub';
        notice.textContent = '최근 20개 대화만 표시돼요.';
        convoList.appendChild(notice);
      }
    } catch (err) {
      convoList.innerHTML = '<p class="sub">' + escapeHtml(err.message) + '</p>';
    }
  }

  function renderConvoCard(item) {
    const card = document.createElement('article');
    card.className = 'convo-card';
    card.dataset.id = item.id;
    card.innerHTML =
      '<div class="row1">' +
      '<span class="title">' + escapeHtml(item.title) + '</span>' +
      '<span class="meta">' + fmtDate(item.updated_at) + ' · ' + item.message_count + '개 메시지 <span class="chevron">▸</span></span>' +
      '</div>' +
      '<div class="preview">눌러서 전체 대화를 확인하세요</div>' +
      '<div class="convo-detail"></div>';

    card.addEventListener('click', async () => {
      const wasOpen = card.classList.contains('open');
      card.classList.toggle('open');
      if (wasOpen) return;

      const detailEl = card.querySelector('.convo-detail');
      detailEl.innerHTML = '<p class="sub">불러오는 중…</p>';
      let detail;
      try {
        detail = await Api.getJSON('/api/conversations/' + item.id);
      } catch (err) {
        detailEl.innerHTML = '<p class="sub">' + escapeHtml(err.message) + '</p>';
        return;
      }
      detailEl.innerHTML =
        detail.messages
          .map((m) => '<div class="line"><b>' + (m.role === 'user' ? '나' : 'AI') + '</b> · ' + escapeHtml(m.content) + '</div>')
          .join('') +
        '<button class="btn secondary continue-btn">이어서 질문하기 →</button>';
      detailEl.querySelector('.continue-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        openConversationInChat(detail);
      });
    });

    return card;
  }

  /* ---------- 5. 데이터 요약 (8.6) ---------- */

  let summaryPending = false;
  async function loadSummary() {
    if (summaryPending) return;
    summaryPending = true;
    Insights.loading();
    document.getElementById("refreshSummary").disabled = true;
    document.querySelectorAll("#view-summary .value, #summaryNet, #summaryCount, #summaryIncome, #summaryExpense, #summaryMonthIncome, #summaryMonthExpense, #summaryMonthNet").forEach(el => { el.textContent = "—"; });
    document.getElementById('summaryPeriod').textContent = '기간 불러오는 중…';
    document.getElementById('summaryTrend').textContent = '불러오는 중…';
    try {
      const s = await Api.getJSON('/api/data/summary');
      const m = s.metrics;
      Insights.update(s);
      updateChatContext(s);

      document.getElementById('summaryPeriod').textContent = (s.period || '기간 정보 없음') + ' · 전체 순증감';
      const netEl = document.getElementById('summaryNet');
      netEl.textContent = won(m.net);
      netEl.className = 'hero-number ' + (m.net >= 0 ? 'positive' : 'negative');

      document.getElementById('summaryCount').textContent = s.count.toLocaleString() + '건';
      document.getElementById('summaryIncome').textContent = wonPlain(m.total_income) + ' (' + m.income_count + '건)';
      document.getElementById('summaryExpense').textContent = wonPlain(m.total_expense) + ' (' + m.expense_count + '건)';
      document.getElementById('summaryAvgIncome').textContent = wonPlain(m.average_income);
      document.getElementById('summaryAvgExpense').textContent = wonPlain(m.average_expense);
      document.getElementById('summaryMax').textContent = won(m.max_transaction);
      document.getElementById('summaryMin').textContent = won(m.min_transaction);

      const cm = s.current_month || {};
      document.getElementById('summaryMonthTitle').textContent = cm.month ? '이번 달 · ' + cm.month : '이번 달';
      document.getElementById('summaryMonthIncome').textContent = wonPlain(cm.income);
      document.getElementById('summaryMonthExpense').textContent = wonPlain(cm.expense);
      const monthNetEl = document.getElementById('summaryMonthNet');
      monthNetEl.textContent = won(cm.net);
      monthNetEl.className = 'amt net ' + (cm.net >= 0 ? 'positive' : 'negative');

      const trendEl = document.getElementById('summaryTrend');
      trendEl.textContent = s.trend || '추세 정보 없음';
      trendEl.className = 'trend-badge';
      if (s.trend && s.trend.includes('증가')) trendEl.classList.add('up');
      else if (s.trend && s.trend.includes('감소')) trendEl.classList.add('down');
    } catch (err) {
      document.getElementById('summaryPeriod').textContent = '요약을 불러오지 못했어요';
      Insights.error(err.message);
    } finally {
      summaryPending = false;
      document.getElementById('refreshSummary').disabled = false;
    }
  }

  document.getElementById('refreshSummary').addEventListener('click', loadSummary);
  function updateChatContext(s) {
    document.getElementById('chatContext').textContent = s.count
      ? `${s.period} · ${s.count.toLocaleString()}건 · 총 지출 ${wonPlain(s.metrics.total_expense)}`
      : '아직 거래가 없어요. 거래 내역에서 기록을 추가해 주세요.';
  }
  Api.getJSON('/api/data/summary').then(updateChatContext).catch(() => {
    document.getElementById('chatContext').textContent = '요약을 불러오지 못했어요. 질문할 때 최신 데이터를 다시 확인합니다.';
  });

  /* ---------- 6. 거래 내역 · 데이터 관리 (8.4) ---------- */

  const dataTableBody = document.getElementById('dataTableBody');
  const dataTableCount = document.getElementById('dataTableCount');
  const paginationEl = document.getElementById('pagination');
  let currentPage = 0;
  let currentTotalCount = 0;

  async function loadDataPage(page) {
    currentPage = page;
    dataTableBody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--muted);">불러오는 중…</td></tr>';
    try {
      const res = await Api.getJSON('/api/data', { limit: PAGE_SIZE, offset: page * PAGE_SIZE });
      currentTotalCount = res.count;
      if (page > 0 && page * PAGE_SIZE >= res.count) { await loadDataPage(Math.max(0, Math.ceil(res.count / PAGE_SIZE) - 1)); return; }
      renderDataTable(res.items);
      renderPagination();
    } catch (err) {
      dataTableBody.innerHTML =
        '<tr><td colspan="5" style="text-align:center;color:var(--brick);">' + escapeHtml(err.message) + '</td></tr>';
      dataTableCount.textContent = '';
    }
  }

  function renderDataTable(items) {
    if (!items.length) {
      dataTableBody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--muted);">표시할 거래가 없어요.</td></tr>';
      dataTableCount.textContent = `전체 ${currentTotalCount.toLocaleString()}건`;
      return;
    }
    dataTableBody.innerHTML = '';
    items.forEach((item) => dataTableBody.appendChild(renderDataRow(item)));
    const start = currentPage * PAGE_SIZE + 1;
    const end = currentPage * PAGE_SIZE + items.length;
    dataTableCount.textContent = `전체 ${currentTotalCount.toLocaleString()}건 중 ${start}–${end} 표시`;
  }

  function renderDataRow(item) {
    const tr = document.createElement('tr');
    tr.dataset.id = item.id;
    const isPositive = item.value >= 0;
    tr.innerHTML =
      '<td>' + escapeHtml(item.date) + '</td>' +
      '<td>' + escapeHtml(item.memo) + '</td>' +
      '<td>' + (item.category ? '<span class="cat-tag">' + escapeHtml(item.category) + '</span>' : '') + '</td>' +
      '<td class="amt ' + (isPositive ? 'positive' : 'negative') + '">' + won(item.value) + '</td>' +
      '<td class="row-actions"><button data-act="edit">수정</button><button data-act="del">삭제</button></td>';
    tr.querySelector('[data-act="edit"]').addEventListener('click', () => openDataModal('edit', item));
    tr.querySelector('[data-act="del"]').addEventListener('click', () => deleteDataRow(item));
    return tr;
  }

  function renderPagination() {
    const totalPages = Math.max(1, Math.ceil(currentTotalCount / PAGE_SIZE));
    paginationEl.innerHTML = '';

    const prevBtn = document.createElement('button');
    prevBtn.textContent = '‹ 이전';
    prevBtn.disabled = currentPage <= 0;
    prevBtn.addEventListener('click', () => loadDataPage(currentPage - 1));

    const label = document.createElement('button');
    label.className = 'current';
    label.textContent = (currentPage + 1) + ' / ' + totalPages;
    label.disabled = true;

    const nextBtn = document.createElement('button');
    nextBtn.textContent = '다음 ›';
    nextBtn.disabled = currentPage >= totalPages - 1;
    nextBtn.addEventListener('click', () => loadDataPage(currentPage + 1));

    paginationEl.append(prevBtn, label, nextBtn);
  }

  async function deleteDataRow(item) {
    if (!confirm('이 거래를 삭제할까요?\n' + item.date + ' · ' + item.memo)) return;
    try {
      await Api.deleteJSON('/api/data/' + item.id);
      showToast('거래를 삭제했어요.');
      await loadDataPage(currentPage);
    } catch (err) {
      showToast(err.message);
    }
  }

  /* ---------- 7. 거래 추가/수정 모달 ---------- */

  const overlay = document.getElementById('modalOverlay');
  const modalTitle = document.getElementById('modalTitle');
  const fieldDate = document.getElementById('fieldDate');
  const fieldMemo = document.getElementById('fieldMemo');
  const fieldCategory = document.getElementById('fieldCategory');
  const fieldValue = document.getElementById('fieldValue');
  let editingItem = null;

  function openDataModal(mode, item) {
    editingItem = item || null;
    modalTitle.textContent = mode === 'edit' ? '거래 수정' : '거래 추가';
    if (item) {
      fieldDate.value = item.date;
      fieldMemo.value = item.memo;
      fieldCategory.querySelectorAll('[data-custom]').forEach(el => el.remove());
      if (item.category && !CATEGORY_OPTIONS.includes(item.category)) {
        const option = new Option(item.category, item.category); option.dataset.custom = 'true'; fieldCategory.add(option);
      }
      fieldCategory.value = item.category || '';
      fieldValue.value = item.value;
    } else {
      fieldDate.value = todayISO();
      fieldMemo.value = '';
      fieldCategory.value = '';
      fieldValue.value = '';
    }
    overlay.classList.add('show');
    fieldDate.focus();
  }

  function closeModal() {
    if (saving) return;
    overlay.classList.remove('show');
    editingItem = null;
  }

  document.getElementById('btnAddRow').addEventListener('click', () => openDataModal('add'));
  document.getElementById('btnModalCancel').addEventListener('click', closeModal);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });

  let saving = false;
  document.getElementById('btnModalSave').addEventListener('click', async () => {
    if (saving) return;
    const date = fieldDate.value;
    const memo = fieldMemo.value.trim();
    const category = fieldCategory.value || null;
    const value = Number(fieldValue.value);

    if (!date || !memo || !Number.isFinite(value) || fieldValue.value.trim() === '') {
      showToast('날짜 · 내용 · 금액을 모두 입력해주세요.');
      return;
    }

    const payload = { date, value, memo, category };
    saving = true;
    document.getElementById("btnModalSave").disabled = true;
    document.getElementById("btnModalCancel").disabled = true;
    try {
      if (editingItem) {
        await Api.putJSON('/api/data/' + editingItem.id, payload);
        showToast('거래를 수정했어요.');
        saving = false;
        closeModal();
        await loadDataPage(currentPage);
      } else {
        await Api.postJSON('/api/data', payload);
        showToast('새 거래를 추가했어요.');
        saving = false;
        closeModal();
        await loadDataPage(0);
      }
    } catch (err) {
      showToast(err.message);
    } finally {
      saving = false;
      document.getElementById("btnModalSave").disabled = false;
      document.getElementById("btnModalCancel").disabled = false;
    }
  });
})();
