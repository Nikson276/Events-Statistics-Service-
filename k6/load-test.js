// k6/load-test.js
import { sleep, check } from 'k6'
import http from 'k6/http'

export const options = {
  thresholds: {
    http_reqs: ['count>=3500']
  },
  stages: [
    { target: 1500, duration: '1m' },
    { target: 2500, duration: '1m30s' },
    { target: 3000, duration: '30s' },
    { target: 3500, duration: '30s' },
  ],
}

export default function () {
  let response

  // Post played track message
  response = http.post(
    'http://fastapi:8000/events/',  // ← ВАЖНО: внутри Docker — не 0.0.0.0!
    JSON.stringify({
      id: `event-${__VU}-${__ITER}`,
      timestamp: new Date().toISOString(),
      track_id: "test-iteration-001",
      user_id: "k6-script"
    }),
    { headers: { 'Content-Type': 'application/json' } }
  )
  check(response, { 'status equals 200': r => r.status === 200 })

//   // Get statistic
//   response = http.get('http://fastapi:8000/events/?limit=10&offset=0')
//   check(response, { 'status equals 200': r => r.status === 200 })

//   sleep(1)
}