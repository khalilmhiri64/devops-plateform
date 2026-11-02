// Find the breaking point. Thresholds are deliberately loose; the goal is the curve.
import { createJob, readPaths } from './lib.js';

export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '2m', target: 150 },
    { duration: '2m', target: 300 },
    { duration: '2m', target: 0 },
  ],
  thresholds: { http_req_failed: [{ threshold: 'rate<0.10', abortOnFail: true, delayAbortEval: '30s' }] },
};

export default function () { readPaths(createJob()); }
