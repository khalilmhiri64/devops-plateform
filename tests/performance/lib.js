import http from 'k6/http';
import { check } from 'k6';

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const JSON_HEADERS = { headers: { 'Content-Type': 'application/json' } };

const SAMPLES = [
  { type: 'wordcount', payload: { text: 'the quick brown fox jumps over the lazy dog' } },
  { type: 'reverse', payload: { text: 'performance testing with k6' } },
  { type: 'fibonacci', payload: { n: 40 } },
  { type: 'prime_check', payload: { n: 1000000007 } },
];

export function createJob() {
  const body = SAMPLES[Math.floor(Math.random() * SAMPLES.length)];
  const res = http.post(`${BASE_URL}/api/jobs`, JSON.stringify(body), { ...JSON_HEADERS, tags: { name: 'POST /api/jobs' } });
  check(res, { 'create: 201': (r) => r.status === 201 });
  return res.status === 201 ? res.json('id') : null;
}

export function readPaths(id) {
  check(http.get(`${BASE_URL}/api/jobs?limit=20`, { tags: { name: 'GET /api/jobs' } }), { 'list: 200': (r) => r.status === 200 });
  check(http.get(`${BASE_URL}/api/stats`, { tags: { name: 'GET /api/stats' } }), { 'stats: 200': (r) => r.status === 200 });
  if (id) {
    check(http.get(`${BASE_URL}/api/jobs/${id}`, { tags: { name: 'GET /api/jobs/:id' } }), { 'get: 200': (r) => r.status === 200 });
  }
}
