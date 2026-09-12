// fetch 공통 래퍼 — 모든 API 호출은 여기(getJSON/postJSON/putJSON/deleteJSON)를 거친다.
// 상태코드별로 에러 메시지를 구분하고, 요청 시작/종료를 onRequestStart/onRequestEnd로 알려서
// 콜드스타트 안내(8.7)를 화면 어디서든 붙일 수 있게 한다.

const Api = (function () {
  'use strict';

  let pendingCount = 0;
  let onRequestStart = null;
  let onRequestEnd = null;

  function setRequestHooks(hooks) {
    onRequestStart = hooks.onStart || null;
    onRequestEnd = hooks.onEnd || null;
  }

  class ApiError extends Error {
    constructor(status, message) {
      super(message);
      this.status = status;
    }
  }

  function statusMessage(status) {
    if (status === 404) return '요청한 항목을 찾을 수 없어요.';
    if (status === 422) return '입력값을 다시 확인해주세요.';
    if (status === 502) return 'AI 응답을 가져오지 못했어요. 잠시 후 다시 시도해주세요.';
    if (status === 500) return '서버에서 오류가 발생했어요. 잠시 후 다시 시도해주세요.';
    return `요청에 실패했어요. (HTTP ${status})`;
  }

  async function handleResponse(res) {
    if (res.ok) {
      if (res.status === 204) return null;
      return res.json();
    }
    let detail = null;
    try {
      const body = await res.json();
      detail = body && body.detail;
    } catch (e) {
      // 본문이 JSON이 아니면 무시하고 아래 기본 메시지를 쓴다.
    }
    throw new ApiError(res.status, detail || statusMessage(res.status));
  }

  function buildUrl(path, params) {
    const url = new URL(API_BASE_URL + path);
    if (params) {
      Object.keys(params).forEach((key) => {
        const value = params[key];
        if (value !== undefined && value !== null && value !== '') {
          url.searchParams.set(key, value);
        }
      });
    }
    return url;
  }

  async function request(method, path, { params, body } = {}) {
    pendingCount += 1;
    if (pendingCount === 1 && onRequestStart) onRequestStart();
    try {
      const url = method === 'GET' ? buildUrl(path, params) : API_BASE_URL + path;
      const options = { method };
      if (body !== undefined) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(body);
      }
      const res = await fetch(url, options);
      return await handleResponse(res);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      // 네트워크 자체가 끊긴 경우(서버 다운, CORS 등) — 콜드스타트 중일 수도 있으니 안내한다.
      throw new ApiError(0, '서버에 연결할 수 없어요. 잠시 후 다시 시도해주세요.');
    } finally {
      pendingCount -= 1;
      if (pendingCount === 0 && onRequestEnd) onRequestEnd();
    }
  }

  return {
    ApiError,
    setRequestHooks,
    getJSON: (path, params) => request('GET', path, { params }),
    postJSON: (path, body) => request('POST', path, { body: body || {} }),
    putJSON: (path, body) => request('PUT', path, { body: body || {} }),
    deleteJSON: (path) => request('DELETE', path),
  };
})();
