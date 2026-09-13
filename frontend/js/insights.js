const Insights = (function () {
  let summary = null;
  const byId = (id) => document.getElementById(id);
  const amount = (n) => Math.round(n).toLocaleString('ko-KR') + '원';
  const escape = (v) => { const el = document.createElement('span'); el.textContent = String(v); return el.innerHTML; };
  function render() {
    if (!summary) return;
    const choice = byId('periodSelect').value;
    const all = summary.monthly || [];
    const rows = choice === 'all' ? all : all.slice(-Number(choice));
    byId('insightContent').hidden = !rows.length;
    byId('exportData').disabled = !rows.length;
    if (!rows.length) { byId('insightStatus').textContent = '아직 거래가 없어요. 거래 내역에서 첫 기록을 추가해 주세요.'; return; }
    const income = rows.reduce((n, r) => n + r.income, 0);
    const expense = rows.reduce((n, r) => n + r.expense, 0);
    const peak = rows.reduce((a, b) => a.expense >= b.expense ? a : b);
    byId('savingsRate').textContent = income ? ((income - expense) / income * 100).toFixed(1) + '%' : '계산할 수 없음';
    byId('monthlyAverage').textContent = amount(expense / rows.length);
    byId('peakMonth').textContent = expense ? peak.month : '지출 없음';
    byId('peakAmount').textContent = expense ? amount(peak.expense) : '선택 기간에 지출 기록이 없어요';
    byId('chartPeriod').textContent = `${rows[0].month} — ${rows[rows.length - 1].month} · ${rows.length}개월`;
    const time = new Date(summary.generated_at);
    byId('insightStatus').textContent = Number.isNaN(time.getTime()) ? '' : `마지막 조회 ${time.toLocaleTimeString('ko-KR')} · 기간 변경은 이 조회 결과에 적용됩니다`;
    byId('monthlyRows').innerHTML = rows.map(r => `<tr><th scope="row">${escape(r.month)}</th><td>${amount(r.income)}</td><td>${amount(r.expense)}</td><td>${amount(r.net)}</td></tr>`).join('');
    const width = Math.max(660, rows.length * 66 + 85), height = 300, top = 20, bottom = 252, left = 72;
    const plot = bottom - top, maximum = Math.max(1, ...rows.flatMap(r => [r.income, r.expense]));
    const ceiling = Math.ceil(maximum / (10 ** Math.floor(Math.log10(maximum)))) * (10 ** Math.floor(Math.log10(maximum)));
    let svg = `<svg viewBox="0 0 ${width} ${height}" style="min-width:${width}px" role="img" aria-labelledby="chartTitle chartDesc"><title id="chartTitle">월별 수입·지출 비교</title><desc id="chartDesc">${escape(byId('chartPeriod').textContent)}. 정확한 수치는 아래 월별 표에서 확인할 수 있습니다.</desc>`;
    for (let i = 0; i <= 4; i++) {
      const value = ceiling * i / 4, y = bottom - plot * i / 4;
      const label = value >= 10000 ? (value / 10000).toLocaleString('ko-KR', { maximumFractionDigits: 1 }) + '만' : Math.round(value).toLocaleString('ko-KR');
      svg += `<line x1="${left}" y1="${y}" x2="${width - 10}" y2="${y}" class="chart-grid"/><text x="${left - 10}" y="${y + 4}" text-anchor="end" class="chart-label">${label}</text>`;
    }
    const step = (width - left - 10) / rows.length;
    rows.forEach((r, index) => {
      const center = left + step * (index + 0.5);
      for (const [key, x, klass, label] of [['income', center - 20, 'chart-income', '수입'], ['expense', center + 2, 'chart-expense', '지출']]) {
        const h = r[key] / ceiling * plot;
        svg += `<rect x="${x}" y="${bottom - h}" width="18" height="${h}" rx="2" class="${klass}"><title>${escape(r.month)} ${label} ${amount(r[key])}</title></rect>`;
      }
      svg += `<text x="${center}" y="${bottom + 23}" text-anchor="middle" class="chart-label">${escape(r.month.slice(2).replace('-', '.'))}</text>`;
    });
    byId('monthlyChart').innerHTML = svg + '</svg>';
  }
  byId('periodSelect').addEventListener('change', render);
  byId('exportData').addEventListener('click', async () => {
    const button = byId('exportData'), format = byId('exportFormat').value, months = byId('periodSelect').value;
    button.disabled = true;
    try {
      const blob = await Api.download('/api/data/export', { format, months });
      const url = URL.createObjectURL(blob), link = document.createElement('a');
      link.href = url; link.download = `transactions-${months}.${format}`; document.body.appendChild(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      byId('insightStatus').textContent = '선택 기간의 전체 거래를 최신 조회해 다운로드했어요.';
    } catch (error) { byId('insightStatus').textContent = '다운로드 실패: ' + error.message; }
    finally { button.disabled = !summary || !summary.monthly?.length; }
  });
  return {
    update: (data) => { summary = data; render(); },
    loading: () => { summary = null; byId('insightContent').hidden = true; byId('exportData').disabled = true; byId('insightStatus').textContent = '소비 흐름을 불러오는 중…'; },
    error: (message) => { summary = null; byId('insightContent').hidden = true; byId('exportData').disabled = true; byId('insightStatus').textContent = message; },
  };
})();
