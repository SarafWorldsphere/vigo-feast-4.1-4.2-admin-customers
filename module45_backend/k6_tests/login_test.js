import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,         // Simulates 5 virtual users
  duration: '5s', // Runs for 5 seconds
  thresholds: {
    // 95% of requests must complete below 2 seconds (2000ms)
    http_req_duration: ['p(95)<2000'],
    // The error rate must be less than 1%
    http_req_failed: ['rate<0.01'],    
  },
};

export default function () {
  // Uses BASE_URL passed via command line, defaulting to http://127.0.0.1:8000
  const baseUrl = __ENV.BASE_URL || 'http://127.0.0.1:8000';

  // Test Overview endpoint
  const resOverview = http.get(`${baseUrl}/api/module45/overview`);
  check(resOverview, {
    'Overview status is 200': (r) => r.status === 200,
  });

  // Test Live Orders endpoint
  const resLiveOrders = http.get(`${baseUrl}/api/module45/live-orders`);
  check(resLiveOrders, {
    'Live Orders status is 200': (r) => r.status === 200,
  });

  sleep(1);
}