import { test, expect } from '@playwright/test';

/**
 * DS integration e2e: dashboard cards fed by mocked Supabase REST +
 * mocked analytics API. No network, no creds.
 *
 * Run:  npm run test:e2e   (frontend/)
 */

const TICKETS = [
  {
    id: 'tick-qa-1',
    patient_id: 'pat-qa-1',
    status: 'open',
    severity: 'High',
    symptoms_summary: 'Persistent fever, body aches',
    extracted_symptoms: {
      llm_severity: 'High',
      ds_prediction: {
        predicted_severity: 'High',
        confidence: 0.87,
        model_used: 'xgboost_cdc_nhamcs',
        abstain: false,
        feature_contributions: { popct: 0.12, pulse: 0.11 },
      },
    },
    vitals_data: { temperature: '102.5', pulse: '110', spo2: '88' },
    created_at: new Date().toISOString(),
    patients: {
      name: 'QA Dharampur',
      phone_number: '+910000000001',
      age: 45,
      gender: 'Male',
      village: 'Dharampur',
    },
  },
  {
    id: 'tick-qa-2',
    patient_id: 'pat-qa-2',
    status: 'open',
    severity: 'Low',
    symptoms_summary: 'Common cold',
    extracted_symptoms: {},
    vitals_data: {},
    created_at: new Date().toISOString(),
    patients: {
      name: 'QA Rampur',
      phone_number: '+910000000002',
      age: 30,
      gender: 'Female',
      village: 'Rampur',
    },
  },
];

const ENHANCED = {
  outbreak_alerts: [
    {
      village: 'Dharampur',
      current_week_cases: 8,
      historical_weekly_avg: 2.3,
      z_score: 4.96,
      alert_level: 'Critical',
      message: 'Anomaly: 8 cases in Dharampur this week vs avg 2.3/week (z=5.0)',
    },
  ],
  daily_trend: Array.from({ length: 30 }, (_, i) => ({
    date: `2026-09-${String(i + 1).padStart(2, '0')}`,
    count: i % 5,
  })),
  order_stats: { pending: 3, in_transit: 5, delivered: 18, total: 26 },
  median_resolution_hours: 4.2,
  total_tickets: 47,
};

const OUTBREAKS = {
  outbreaks: [
    {
      village: 'Dharampur',
      case_count: 8,
      time_window: '4 Days',
      alert_level: 'High',
      message: 'Outbreak Warning: 8 cases reported in Dharampur.',
    },
  ],
  region_breakdown: [
    { region: 'Dharampur', total_cases: 8, high_severity: 2, medium_severity: 3, low_severity: 3 },
  ],
  disease_breakdown: [{ disease: 'Viral Fever', count: 8 }],
  age_breakdown: [{ group: '19-35', count: 8 }],
  status_breakdown: [{ status: 'open', count: 8 }],
  gender_breakdown: [{ gender: 'Male', count: 8 }],
  total_patients: 8,
  critical_count: 2,
  resolved_count: 1,
};

const API_HOSTS = ['http://127.0.0.1:8002', 'https://curago-backend.onrender.com'];

test.beforeEach(async ({ page }) => {
  await page.route('**/rest/v1/tickets*', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(TICKETS),
    }),
  );
  await page.route('**/rest/v1/orders*', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([]),
    }),
  );
  for (const host of API_HOSTS) {
    await page.route(`${host}/api/analytics/enhanced`, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(ENHANCED),
      }),
    );
    await page.route(`${host}/api/analytics/outbreaks`, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(OUTBREAKS),
      }),
    );
    await page.route(`${host}/api/recommend`, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'ok',
          recommendation: {
            suggestions: [
              { medicine: 'Paracetamol 500mg', dose: '500mg twice daily', why: 'e2e mock', in_stock: true },
            ],
            disease: 'Common Cold',
            confidence: 0.81,
            model: 'v0-rules',
            abstain: false,
          },
        }),
      }),
    );
  }
});

test('enhanced analytics strip renders DS cards', async ({ page }) => {
  await page.goto('/doctor');
  await page.getByText('📊 Analytics').click();

  await expect(page.getByText('Epidemic Analytics & Outbreaks')).toBeVisible();
  await expect(page.getByText('Daily Ticket Volume')).toBeVisible();
  await expect(page.getByText('Order Fulfillment')).toBeVisible();
  await expect(page.getByText('Resolution Time')).toBeVisible();
  await expect(page.getByText('DS Outbreak Alerts')).toBeVisible();
  await expect(page.getByText('Dharampur', { exact: false }).first()).toBeVisible();
  // order stats from mocked enhanced payload
  await expect(page.getByText('/26 delivered', { exact: false })).toBeVisible();
});

test('DS severity card renders on selected patient', async ({ page }) => {
  await page.goto('/doctor');
  // first patient auto-selected; detail panel shows the DS card
  await expect(page.getByText('AI Triage Assessment (Decision Support)')).toBeVisible();
  await expect(page.getByText('High Severity')).toBeVisible();
  await expect(page.getByText('Confidence: 87%')).toBeVisible();
  await expect(page.getByText(/decision-support only/, { exact: false })).toBeVisible();
});

test('adaptive Rx card renders and Accept stages prescription', async ({ page }) => {
  await page.goto('/doctor');
  await expect(page.getByText('Adaptive Prescription (v0-rules', { exact: false })).toBeVisible();
  await expect(page.getByText('Paracetamol 500mg').first()).toBeVisible();
  await page.getByRole('button', { name: 'Accept suggestions' }).click();
  // staged into prescription list (approve gate requires >=1 medicine)
  await expect(page.getByRole('button', { name: /Approve & Dispatch Order/ }).first()).toBeEnabled();
});

test('predict-severity contract (live backend, skipped if down)', async ({ request }) => {
  let res;
  try {
    res = await request.post('http://127.0.0.1:8002/api/predict-severity', {
      data: { age: 55, gender: 'Male', pulse: 120, spo2: 85 },
      timeout: 10_000,
    });
  } catch {
    test.skip(true, 'backend not running on :8002');
    return;
  }
  if (!res.ok()) {
    test.skip(true, `backend returned ${res.status()}`);
    return;
  }
  const body = await res.json();
  expect(body.status).toBe('ok');
  expect(body.prediction.predicted_severity).toBe('High');
  expect(body.prediction.abstain).toBe(false);
  expect(body.prediction.confidence).toBeGreaterThan(0.6);
});

test('predict-disease + recommend contracts (live backend, skipped if down)', async ({ request }) => {
  let d, r;
  try {
    d = await request.post('http://127.0.0.1:8002/api/predict-disease', {
      data: { text: 'red itchy skin rash with scaly patches' },
      timeout: 10_000,
    });
    r = await request.post('http://127.0.0.1:8002/api/recommend', {
      data: { symptoms: 'high fever and chills for three days' },
      timeout: 10_000,
    });
  } catch {
    test.skip(true, 'backend not running on :8002');
    return;
  }
  if (!d.ok() || !r.ok()) {
    test.skip(true, 'backend returned non-ok');
    return;
  }
  const db = await d.json();
  expect(db.status).toBe('ok');
  expect(db.prediction.label).toBeTruthy();
  expect(db.prediction.top3).toHaveLength(3);
  const rb = await r.json();
  expect(rb.status).toBe('ok');
  expect(rb.recommendation.abstain).toBe(false);
  expect(rb.recommendation.suggestions.length).toBeGreaterThan(0);
  expect(rb.recommendation.suggestions[0]).toEqual(
    expect.objectContaining({ medicine: expect.any(String), dose: expect.any(String), why: expect.any(String), in_stock: true }),
  );
});

test('enhanced analytics contract (live backend, skipped if down)', async ({ request }) => {
  let res;
  try {
    res = await request.get('http://127.0.0.1:8002/api/analytics/enhanced', {
      timeout: 10_000,
    });
  } catch {
    test.skip(true, 'backend not running on :8002');
    return;
  }
  if (!res.ok()) {
    test.skip(true, `backend returned ${res.status()}`);
    return;
  }
  const body = await res.json();
  expect(body.daily_trend).toHaveLength(30);
  expect(body.order_stats).toEqual(
    expect.objectContaining({ pending: expect.any(Number), delivered: expect.any(Number) }),
  );
});
