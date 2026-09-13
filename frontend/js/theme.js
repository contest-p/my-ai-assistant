// 먼저 적용해 저장된 테마와 첫 화면의 색이 다르게 깜빡이지 않도록 한다.
(function () {
  let saved;
  try { saved = localStorage.getItem('finance-theme'); } catch (_) { /* 저장 제한 환경 */ }
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  document.documentElement.dataset.theme = saved || (system.matches ? 'dark' : 'light');
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('themeToggle');
    function sync() {
      const dark = document.documentElement.dataset.theme === 'dark';
      button.textContent = dark ? '라이트 모드로' : '다크 모드로';
      button.setAttribute('aria-pressed', String(dark));
    }
    button.addEventListener('click', () => {
      saved = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = saved;
      try { localStorage.setItem('finance-theme', saved); } catch (_) { /* 현재 탭에만 적용 */ }
      sync();
    });
    system.addEventListener('change', () => {
      if (!saved) { document.documentElement.dataset.theme = system.matches ? 'dark' : 'light'; sync(); }
    });
    sync();
  });
})();
