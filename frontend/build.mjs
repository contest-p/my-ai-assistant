// Vercel 환경변수에서 공개 API 주소만 정적 설정으로 만든다. 프레임워크·외부 패키지 없음.
import { mkdir, cp, writeFile } from 'node:fs/promises';

const raw = process.env.API_BASE_URL;
if (!raw) throw new Error('API_BASE_URL 환경변수를 설정해주세요.');
const url = new URL(raw);
if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
  throw new Error('API_BASE_URL은 인증정보·쿼리가 없는 HTTP(S) 주소여야 합니다.');
}
if (process.env.VERCEL && url.protocol !== 'https:') throw new Error('배포 API 주소에는 HTTPS가 필요합니다.');
await mkdir('dist/js', { recursive: true });
await cp('index.html', 'dist/index.html');
await cp('css', 'dist/css', { recursive: true });
await cp('js', 'dist/js', { recursive: true });
await writeFile('dist/js/config.js', `const API_BASE_URL = ${JSON.stringify(raw.replace(/\/+$/, ''))};\n`);
