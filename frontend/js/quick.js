const QuickLookup = (function () {
  'use strict';
  const monthSelect = document.getElementById('quickMonth');
  const buttons = [...document.querySelectorAll('[data-quick]')];
  const status = document.getElementById('quickStatus');
  const result = document.getElementById('quickResult');
  const titles = { summary: '입금·출금 요약', largest: '가장 큰 출금 5건', expenses: '출금 내역', income: '입금 내역' };
  let pending = false;
  let activeKind = null;
  let initialized = false;
  const amount = value => Number(value).toLocaleString('ko-KR', { maximumFractionDigits: 2 }) + '원';
  function escape(value) {
    const el = document.createElement('span');
    el.textContent = value == null ? '' : String(value);
    return el.innerHTML;
  }
  function setMonths(months, preferred) {
    const sorted = [...new Set(months)].sort().reverse();
    const chosen = preferred ?? (initialized ? monthSelect.value : sorted[0] || 'all');
    const options = [new Option('전체 기간', 'all'), ...sorted.map(month => new Option(month, month))];
    // 조회 중 삭제된 월도 결과의 기간과 선택값을 일치시킨다.
    if (chosen !== 'all' && !sorted.includes(chosen)) options.push(new Option(chosen + ' (거래 없음)', chosen));
    monthSelect.replaceChildren(...options);
    monthSelect.value = chosen;
    if (sorted.length || preferred !== undefined) initialized = true;
  }
  function render(data) {
    const scope = data.month === 'all' ? '전체 기간' + (data.period ? ' · ' + data.period : '') : data.month;
    let html = '<h3>' + escape(scope) + ' · ' + titles[data.kind] + '</h3>';
    if (data.kind === 'summary') {
      html += '<dl class="quick-totals"><div><dt>입금 · ' + data.income_count + '건</dt><dd>' + amount(data.income) + '</dd></div>' +
        '<div><dt>출금 · ' + data.expense_count + '건</dt><dd>' + amount(data.expense) + '</dd></div>' +
        '<div><dt>순유입</dt><dd>' + (data.net > 0 ? '+' : '') + amount(data.net) + '</dd></div></dl>';
      if (!data.count) html += '<p>선택한 기간에 거래가 없어요.</p>';
    } else if (!data.items.length) {
      html += '<p>선택한 기간에 ' + (data.kind === 'income' ? '입금' : '출금') + ' 내역이 없어요.</p>';
    } else {
      html += '<ol class="quick-records" start="' + (data.offset + 1) + '">' + data.items.map(row =>
        '<li><div><span class="quick-date">' + escape(row.date) + '</span><strong>' + escape(row.memo) + '</strong>' +
        '<span class="quick-category">' + escape(row.category ?? '미분류') + '</span></div>' +
        '<span class="quick-amount">' + amount(Math.abs(row.value)) + '</span></li>').join('') + '</ol>';
      html += '<p class="sub">' + (data.offset + 1) + '–' + (data.offset + data.items.length) + '건 표시 · 전체 ' + data.total + '건' +
        (data.kind === 'largest' ? ' 중 금액 상위' : '') + '</p>';
      if (data.kind !== 'largest' && (data.offset > 0 || data.has_more)) {
        html += '<div class="quick-pages"><button class="btn secondary" data-page="prev"' + (data.offset === 0 ? ' disabled' : '') +
          '>이전</button><button class="btn secondary" data-page="next"' + (!data.has_more ? ' disabled' : '') + '>다음</button></div>';
      }
    }
    result.innerHTML = html;
    result.hidden = false;
    result.querySelector('[data-page="prev"]')?.addEventListener('click', () => lookup(data.kind, Math.max(0, data.offset - data.limit)));
    result.querySelector('[data-page="next"]')?.addEventListener('click', () => lookup(data.kind, data.offset + data.limit));
  }
  async function lookup(kind, offset = 0) {
    if (pending) return;
    pending = true;
    activeKind = kind;
    const month = monthSelect.value;
    monthSelect.disabled = true;
    buttons.forEach(button => { button.disabled = true; button.setAttribute('aria-pressed', String(button.dataset.quick === kind)); });
    result.hidden = true;
    result.setAttribute('aria-busy', 'true');
    status.textContent = '기록을 확인하는 중…';
    try {
      const data = await Api.getJSON('/api/data/quick-answer', { kind, month, offset });
      setMonths(data.months, month);
      render(data);
      status.textContent = '기록에서 확인한 결과예요. ' + new Date().toLocaleTimeString('ko-KR') + ' 조회';
    } catch (error) {
      status.textContent = '조회하지 못했어요. ' + error.message + ' 항목을 눌러 다시 시도해 주세요.';
    } finally {
      pending = false;
      monthSelect.disabled = false;
      buttons.forEach(button => { button.disabled = false; });
      result.setAttribute('aria-busy', 'false');
    }
  }
  buttons.forEach(button => button.addEventListener('click', () => lookup(button.dataset.quick)));
  monthSelect.addEventListener('change', () => { if (activeKind) lookup(activeKind); });
  return { setMonths: months => { if (!pending) setMonths(months); } };
})();
