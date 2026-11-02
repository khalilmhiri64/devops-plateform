// Sustained, realistic load (read-heavy). Run nightly against staging.
import { sleep } from 'k6';
import { createJob, readPaths } from './lib.js';

export const options = {
  scenarios: {
    writers: { executor: 'constant-arrival-rate', rate: 20, timeUnit: '1s', duration: '5m',
               preAllocatedVUs: 20, maxVUs: 50, exec: 'write' },
    readers: { executor: 'ramping-vus', startVUs: 0, exec: 'read',
               stages: [{ duration: '1m', target: 50 }, { duration: '3m', target: 50 }, { duration: '1m', target: 0 }] },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    'http_req_duration{name:POST /api/jobs}': ['p(95)<400'],
    'http_req_duration{name:GET /api/jobs}': ['p(95)<250'],
  },
};

export function write() { createJob(); }
export function read() { readPaths(null); sleep(0.5); }
