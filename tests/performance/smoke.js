// Quick quality gate run on every build and after every deployment.
import { sleep } from 'k6';
import { createJob, readPaths } from './lib.js';

export const options = {
  vus: 5,
  duration: '30s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<300'],
    checks: ['rate>0.99'],
  },
};

export default function () {
  readPaths(createJob());
  sleep(1);
}
