// ============================================================
// 목업 인터랙션 스크립트 (실제 API 호출 없음 — 화면 흐름 데모용)
// ============================================================

(function () {
  'use strict';

  /* ---------- 1. 사이드바 / 모바일 탭 전환 ---------- */

  const navButtons = document.querySelectorAll('.nav-item, .mobile-topbar button');
  const views = document.querySelectorAll('.view');

  function switchView(viewName) {
    views.forEach((v) => v.classList.toggle('active', v.id === 'view-' + viewName));
    navButtons.forEach((b) => b.classList.toggle('active', b.dataset.view === viewName));
  }

  navButtons.forEach((btn) => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });

  /* ---------- 2. 채팅 데모 ---------- */

  const chatLog = document.getElementById('chatLog');
  const chatInput = document.getElementById('chatInput');
  const btnSend = document.getElementById('btnSend');
  const typingMsg = document.getElementById('typingMsg');

  const demoReplies = [
    '데이터를 다시 확인해봤어요. 최신 요약 기준으로는 아직 큰 변화는 없어요.',
    '좋은 질문이에요 — 관련 수치를 요약에서 찾아봤는데, 지금 기준으로는 안정적인 편이에요.',
    '그 부분은 이번 달 데이터를 기준으로 답하면, 평소와 크게 다르지 않아요.'
  ];

  function appendMessage(role, html) {
    const wrap = document.createElement('div');
    wrap.className = 'msg ' + role;
    wrap.innerHTML = '<div class="bubble">' + html + '</div>';
    chatLog.insertBefore(wrap, typingMsg);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    appendMessage('user', escapeHtml(text));
    chatInput.value = '';

    typingMsg.style.display = 'flex';
    chatLog.scrollTop = chatLog.scrollHeight;

    setTimeout(() => {
      typingMsg.style.display = 'none';
      const reply = demoReplies[Math.floor(Math.random() * demoReplies.length)];
      appendMessage('ai', reply + '<span class="figures">(목업 데모 응답)</span>');
    }, 1100);
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  btnSend.addEventListener('click', sendMessage);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendMessage();
  });

  document.getElementById('btnDemoLoading').addEventListener('click', () => {
    typingMsg.style.display = typingMsg.style.display === 'flex' ? 'none' : 'flex';
    chatLog.scrollTop = chatLog.scrollHeight;
  });

  document.getElementById('btnDemoColdstart').addEventListener('click', () => {
    document.getElementById('coldstartNote').classList.toggle('show');
  });

  /* ---------- 3. 대화 기록 아코디언 ---------- */

  document.querySelectorAll('.convo-card').forEach((card) => {
    card.addEventListener('click', (e) => {
      card.classList.toggle('open');
    });
  });

  /* ---------- 4. 거래 내역 CRUD 모달 ---------- */

  const overlay = document.getElementById('modalOverlay');
  const modalTitle = document.getElementById('modalTitle');
  const fieldDate = document.getElementById('fieldDate');
  const fieldMemo = document.getElementById('fieldMemo');
  const fieldCategory = document.getElementById('fieldCategory');
  const fieldValue = document.getElementById('fieldValue');
  const tableBody = document.getElementById('dataTableBody');
  let editingRow = null;

  function openModal(mode, row) {
    editingRow = row || null;
    modalTitle.textContent = mode === 'edit' ? '거래 수정' : '거래 추가';
    if (row) {
      const cells = row.querySelectorAll('td');
      fieldDate.value = cells[0].textContent;
      fieldMemo.value = cells[1].textContent;
      fieldCategory.value = cells[2].textContent.trim();
      fieldValue.value = cells[3].textContent.replace(/[^0-9-]/g, '');
    } else {
      fieldDate.value = '2026-09-08';
      fieldMemo.value = '';
      fieldCategory.value = '카드결제';
      fieldValue.value = '';
    }
    overlay.classList.add('show');
  }

  function closeModal() {
    overlay.classList.remove('show');
    editingRow = null;
  }

  document.getElementById('btnAddRow').addEventListener('click', () => openModal('add'));
  document.getElementById('btnModalCancel').addEventListener('click', closeModal);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });

  document.getElementById('btnModalSave').addEventListener('click', () => {
    const value = parseInt(fieldValue.value || '0', 10);
    const isPositive = value >= 0;
    const formatted = (isPositive ? '+' : '−') + Math.abs(value).toLocaleString() + '원';

    if (editingRow) {
      const cells = editingRow.querySelectorAll('td');
      cells[0].textContent = fieldDate.value;
      cells[1].textContent = fieldMemo.value || '(내용 없음)';
      cells[2].innerHTML = '<span class="cat-tag">' + fieldCategory.value + '</span>';
      cells[3].textContent = formatted;
      cells[3].className = 'amt ' + (isPositive ? 'positive' : 'negative');
      showToast('거래를 수정했어요.');
    } else {
      const tr = document.createElement('tr');
      tr.innerHTML =
        '<td>' + fieldDate.value + '</td>' +
        '<td>' + (fieldMemo.value || '(내용 없음)') + '</td>' +
        '<td><span class="cat-tag">' + fieldCategory.value + '</span></td>' +
        '<td class="amt ' + (isPositive ? 'positive' : 'negative') + '">' + formatted + '</td>' +
        '<td class="row-actions"><button data-act="edit">수정</button><button data-act="del">삭제</button></td>';
      tableBody.insertBefore(tr, tableBody.firstChild);
      bindRowActions(tr);
      showToast('새 거래를 추가했어요.');
    }
    closeModal();
  });

  function bindRowActions(row) {
    row.querySelectorAll('button').forEach((btn) => {
      btn.addEventListener('click', () => {
        if (btn.textContent === '수정') {
          openModal('edit', row);
        } else {
          row.remove();
          showToast('거래를 삭제했어요.');
        }
      });
    });
  }

  document.querySelectorAll('#dataTableBody tr').forEach(bindRowActions);

  /* ---------- 5. 토스트 ---------- */

  let toastTimer;
  function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
  }

})();
