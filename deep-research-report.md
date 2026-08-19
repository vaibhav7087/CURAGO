# Executive Summary  
Building reliable telephone-based voice agents (SIP/VoIP) demands rigorous testing beyond typical API tests.  Voice-specific failures – e.g. latency, misrecognized speech, audio glitches – occur in roughly 40% of real production calls, yet they are *not* caught by transcript-only tests.  Likewise, SIP-layer issues (registration failures, one-way audio, codec mismatches) must be uncovered before live deployment.  This report outlines a comprehensive test plan for the *CURAGO* voice-agent repository, focusing on **pre-call validation** (logic/unit tests and mocks to avoid real calls), **in-call simulation tests**, and **post-call monitoring/logging checks**.  We list test categories (input validation, authentication, error handling, concurrency, etc.), detailed test-case templates (purpose, steps, expected, data, priority, runtime, automation), and strategies for mocking SIP/VoIP (e.g. Twilio test credentials or SIP test tools) to minimise costly live calls.  We also define observability requirements (structured JSON logging, metrics from Twilio Voice Insights, tracing spans, and alert rules) and CI/CD integration guidelines.  Mermaid diagrams illustrate the system architecture, example call-test flows, and a suggested CI pipeline. All recommendations draw on official best-practice sources (e.g. Twilio docs, SIP testing guides, Python logging guidance).  

## System Architecture (High-Level)  
```mermaid
graph LR
  A[(User Phone / SIP Client)] -->|SIP/PSTN| B[Telephony Provider (e.g. Twilio SIP Interface)]
  B --> C[CURAGO Voice Agent (Application Server)]
  C --> D[NLU/AI Service (Speech-to-Text / LLM)]
  C --> E[(Database / App Server)]
  C --> F[Logging/Monitoring Stack]
  C --> G[Metrics Collector / Alerting]
  C --> H[Web/API Endpoints (Admin/UI)]  
  A2[(Inbound Caller)] -->|SIP/PSTN| B
```
**Figure:** CURAGO voice-agent components and call flow (user phones ↔ SIP provider ↔ agent code ↔ AI service/DB).  The voice agent uses a SIP interface (e.g. Twilio, Asterisk, FreeSWITCH) to send/receive calls.  Internally it may call NLP/AI services (for ASR/NLU) and store call records in a database.  All events (call start/end, errors, user utterances) should be logged to a structured logging system and emitted as metrics/traces for monitoring.

## Test Strategy Overview  
Specialised voice-agent testing spans **three phases**: 

- **Pre-Call Validation (Offline)** – Unit and logic tests that verify inputs, configurations, and control flows before attempting any real call. This includes static checks (e.g. phone number formats, config parsing, authorization), and **mocked call flows** (simulated SIP exchanges or Twilio test mode) to validate call logic without network.  
- **In-Call Simulation** – End-to-end tests that simulate real voice calls (via PSTN/SIP or emulators) to verify interaction flows, ASR/TTS handling, DTMF, timeouts, concurrent calls, and error responses.  For cost control, many in-call tests should use *mock telephony* (e.g. SIP simulators like SIPp or Twilio’s “Test Credentials”), with only a minimal set of live calls for smoke-testing in staging.  
- **Post-Call Monitoring & Recovery** – Tests of logging, databases, and analytics after calls. This includes verifying that call logs can be retrieved (e.g. via the Telephony provider’s API), call status is recorded correctly, and that alerts/metrics detect anomalies (see Observability below).  

Our design follows the four-layer quality framework for voice systems: **Functional correctness**, **SIP signaling and media quality**, **load/scale behaviour**, and **observability/security**.  For example, Hamming’s voice-agent QA criteria emphasize end-to-end PSTN/SIP call simulation, latency/ASR metrics, conversational turn-taking, concurrency, plus integration and reporting.  This plan incorporates all these aspects.

## Repository Structure & Services to Test  
While the exact CURAGO codebase is proprietary, we assume it provides: 
- **Call initiation service** (functions to place outgoing calls or answer incoming calls).  
- **Call session handler** (manages each call’s state: prompts, ASR, dialogue logic).  
- **External interfaces**: SIP/Twilio API, database (e.g. patient records), maybe REST admin endpoints.  
- **Config/environment**: telephone credentials (SIP URIs, API keys), DB connection, feature flags.  
- **Logging/metrics hooks**.  

**Services/Endpoints to test** might include (hypothetical examples):  
- `POST /calls` – initiate a new call (input: phone number, patient ID).  
- Webhook callback endpoints for call events (SIP INVITE, user DTMF, transcription results).  
- Functions like `validatePhoneNumber()`, `scheduleCall()`, `handleAnswer()`, `recordOutcome()`.  
- Database queries/update functions for call records.  
- Admin APIs for checking call logs or adjusting settings.  

We recommend mapping out each service or function and writing unit tests and integration tests for it.  For every external API (e.g. Twilio Voice API or SIP library calls), plan to mock responses.

## Pre-Call (Unit/Mocked) Test Cases  
These tests run without placing a real call, using mocks or dry-run logic to catch errors early.  **Categories of tests include:**  

- **Input Validation (Unit Tests)**: Verify all input data to call-related functions. Examples:  
  - **Phone number formats**: valid E.164 numbers, invalid numbers (letters, too short/long), missing “+” or country code.  
  - **User data constraints**: e.g. patient ID must exist (use DB mocks), appointment times must be in the future.  
  - **Configuration values**: missing or malformed config (e.g. missing SIP domain or credentials) should raise errors.  
  - **API request validation**: if there is a REST endpoint, test invalid HTTP payloads, missing fields, incorrect JSON schema.  

- **Authentication/Authorization**: If there are protected APIs (e.g. admin dashboard), test scenarios for: valid credentials/tokens (access granted) vs invalid/expired tokens (403 Forbidden).  Ensure all secrets (e.g. API keys) are read securely from environment (mock env vars).  

- **Error Handling and Exception Paths**: Simulate failure modes in dependencies (e.g. database connection error, network unreachable, SIP failure codes). Each path should be exercised: e.g. mock a SIP 503 response and verify it is retried or logged properly.  

- **Boundary & Edge Cases**: E.g. maximum allowable concurrent calls (if limited by config), zero or negative values for durations or IDs, time-zone edge (midnight), special characters in user data.  

- **Rate-limiting and Retry Logic**: If the system has logic to throttle calls (e.g. at most X calls per minute) or to retry failed calls (e.g. after busy signal), write tests that mock successive call attempts. For instance, configure a “limit of 2 calls/minute”, then attempt 3 calls and expect the 3rd to be blocked or deferred.  

- **Dependency Mocks**: All external interactions (SIP/Twilio API, database, AI/NLP service) should be mocked in unit tests. For example, use a mock SIP server or stub Twilio’s HTTP API to return canned call SIDs/status. Verify that, given a “successful call initiation” response, the code proceeds correctly; and given a “failure” response, it handles the exception as expected.  

- **Data Integrity (Unit-Level)**: E.g. if calls update a database (marking an appointment complete), mock the DB and check that writes are made in the correct order, and rolled back on error. Test transaction atomicity (e.g. mock a mid-call failure and ensure no partial data persisted).  

**Sample Pre-Call Test Case (Unit)**: 

- **Test Case**: TC-Pre-01: *Invalid Phone Number Format*  
  - **Purpose**: Ensure system rejects malformed numbers before attempting a call.  
  - **Preconditions**: Call-scheduling code is initialized with default config.  
  - **Steps**: Call the validation function with input `"ABC123"`.  
  - **Expected Result**: The function throws a validation exception (HTTP 400 or error) indicating invalid format. No call attempt is made.  
  - **Test Data**: `"ABC123"`, `"12345"`, `"++0123456789"` (test a few malformed samples).  
  - **Priority**: High.  
  - **Estimated Runtime**: ~0.1s (unit test).  
  - **Automation**: Automated.  

- **Test Case**: TC-Pre-02: *Valid Phone Number Leading Plus*  
  - **Purpose**: Verify acceptance of properly formatted number.  
  - **Preconditions**: Same as above.  
  - **Steps**: Call validation with `"+441632960960"` (UK number).  
  - **Expected Result**: Validation succeeds (return normalized format or true).  
  - **Data**: Example valid numbers.  
  - **Priority**: High.  
  - **Runtime**: ~0.1s. Automated.  

- **Test Case**: TC-Pre-03: *Missing Twilio/SIP Credentials*  
  - **Purpose**: Confirm system fails fast if auth config is absent.  
  - **Preconditions**: Environment variable for SIP credentials is unset.  
  - **Steps**: Start call service; attempt to place any call.  
  - **Expected Result**: System throws configuration error (logs an error, returns 500). Alert should be triggered (see monitoring).  
  - **Priority**: Critical.  
  - **Runtime**: ~0.2s (unit). Automated.  

- **Test Case**: TC-Pre-04: *Database Down on Appointment Lookup*  
  - **Purpose**: Ensure graceful handling when DB is unavailable.  
  - **Preconditions**: Mock DB query to throw connection error.  
  - **Steps**: Invoke function to fetch appointment by ID.  
  - **Expected Result**: Code catches exception, returns an appropriate error (e.g. HTTP 503), and logs the error. No call is attempted.  
  - **Priority**: High.  
  - **Runtime**: ~0.2s. Automated.  

*(Additional unit tests should cover each branch of code: error vs success, edge values, every config flag, etc.)*

## In-Call (Integration/Simulation) Test Cases  
These tests involve simulating or making calls to exercise the actual voice flow and telephony behavior.  We recommend **mocked/instrumented calls** for most scenarios to save cost.  For example, Twilio provides “Test Credentials” and special numbers that simulate different call outcomes (busy, no-answer, completed) without incurring charges.  Likewise, SIP testing tools like **SIPp** or a local stub server (per [TestMu AI] recommendations) can generate call signaling flows.

Key in-call test categories:  

- **Call Setup and Teardown**: Verify that the entire SIP/VoIP handshake works. Using a test SIP client or Twilio test mode:  
  - Simulate a successful call setup (100 TRYING, 200 OK) and teardown (BYE) and verify agent responds correctly (e.g. plays greeting).  
  - Simulate busy/hangup scenarios: e.g. the callee busy (SIP 486 Busy Here) or no answer (timeout). The agent should detect this and handle (log error, retry or abort).  
  - Simulate SIP OPTIONS ping (health-check) to ensure trunk is up.  

- **Conversation Flow (Voice/DTMF Interactions)**: If the agent has an IVR or voice-AI flow:  
  - Provide known audio inputs (using audio files or synthesized voice) for each expected user prompt. E.g. user says “yes” or presses “1” as expected, and verify the next prompt.  
  - Test *invalid input* cases (background noise, unsupported language) and verify the agent’s fallback (e.g. “Sorry, I didn’t catch that”).  
  - Barge-in/interruption: during agent’s prompt, provide user speech and verify agent can handle it (based on barge-in support).  

- **Timing/Timeouts**: Test behavior when the user is silent or a response takes too long. E.g.:  
  - No user response for X seconds triggers a reprompt or ends the call.  
  - ASR service latency: artificially delay the NLP response and check for agent timeouts or TTS delay.  

- **Audio Quality / Codecs**: Ensure calls can negotiate codecs properly. For example, if agent and caller share a codec (e.g. G.711 ulaw), verify audio loopback.  Use Wireshark or `sngrep` to inspect SIP/RTP as per .  

- **Concurrency/Stress**: Load-testing with multiple simultaneous calls:  
  - Use **SIPp** to initiate N concurrent calls (e.g. up to expected peak, say 50+) and confirm the agent handles them (no crashes, proper queueing).  Verify that call routing (threads or processes) works without race conditions.  
  - Test database and resource locks under concurrency (e.g. two calls updating same appointment).  

- **Failure Injection**: During a call, simulate mid-call failures: e.g. force a network drop or raise an exception in mid-flow. The agent should log the error and cleanly end the call.  

- **External Integration**: If the agent calls out to other services (NLU, CRM), test them in the loop: For integration tests you may either use a staging NLP service or mock its webhook. Ensure that the full chain (call > ASR > NLP > call) works end-to-end.

**Sample In-Call Test Case (Simulated)**: 

- **Test Case**: TC-InCall-01: *Outgoing Call, Busy Signal*  
  - **Purpose**: Verify retry or failure logic when target is busy.  
  - **Preconditions**: Configure SIP/Twilio test number that returns Busy.  
  - **Steps**: Trigger an outbound call via the API to that number.  
  - **Expected Result**: Agent receives busy SIP response; should log “callee busy”, attempt a configurable number of retries (or give up), and record the final failure status. No further prompts should be played.  
  - **Data**: Twilio’s “+15005550001” for busy (if using Twilio test credentials).  
  - **Priority**: High.  
  - **Runtime**: ~5s (end-to-end). Automated (using SIPp or Twilio test).  

- **Test Case**: TC-InCall-02: *Inbound Call, Voice Prompt and Response*  
  - **Purpose**: Test normal inbound flow.  
  - **Preconditions**: Register a SIP softphone on agent, or use Twilio to forward an incoming call.  
  - **Steps**: Using a SIP client, place a call to the agent’s number. On answer, play a prerecorded “yes” audio (simulate user confirming).  
  - **Expected Result**: Agent plays welcome prompt, receives “yes”, then proceeds to next intent (e.g. “Great, connecting you to...” or ends call with success).  
  - **Data**: Audio file of user saying “yes”.  
  - **Priority**: High.  
  - **Runtime**: ~10s (speaking time). Semi-automated (requires audio playback).  

*(Add tests for inbound unknown input, timeouts, error in TTS, etc.)*

## Post-Call and Monitoring Test Cases  
After a call ends, the system should update records and emit relevant metrics/logs. Test scenarios include:  

- **Call Log Retrieval**: After a call, use the Telephony API (e.g. Twilio Calls API) to fetch the call record. Verify that the stored status (completed/failed), duration, and SIP details match expectations. For example, Twilio’s `GET /Calls/{CallSid}` should return a record whose `status` matches the agent’s final state.  

- **Database Record Integrity**: If calls create or update DB entries (e.g. mark “appointment_reminder_sent”), verify those records were created with correct timestamps and fields. Check transactions: ensure no “half-written” data if a call aborted.  

- **Logging Verification**: Ensure that every call generates structured logs with key fields (call ID, timestamps, status, error codes).  For example, at the end of each call the log might include `{"event": "CALL_END", "call_id": "...", "duration": 45, "result": "COMPLETED"}`. Tests can parse captured logs (from log files or log management) to assert these fields appear.  

- **Metrics and Alerts**: Simulate failure conditions to trigger alerts. For instance, configure alerts on high failure rates: if 3 out of 5 simulated calls fail, the system should emit an alert to monitoring. Use a test metrics backend (e.g. push test metrics to Prometheus) and assert that the alert condition would fire.  

**Sample Post-Call Test Case**:  

- **Test Case**: TC-Post-01: *Call Failure Metric Ingestion*  
  - **Purpose**: Ensure call-failure events increment metrics and trigger alerts.  
  - **Preconditions**: Set a threshold metric rule (e.g. alert if failure_rate > 50%).  
  - **Steps**: Execute 2 successful calls and 2 simulated failed calls (e.g. busy).  
  - **Expected Result**: Metrics should show `call_total=4, call_failures=2 (50%)`. The alert condition is met (50% failures) – an alert event/log is produced.  
  - **Data**: Use metrics names “calls_succeeded”, “calls_failed”.  
  - **Priority**: Medium.  
  - **Runtime**: ~10s. Automated (assert metrics).  

## Observability (Logging, Metrics, Traces, Alerts)  
Effective monitoring is crucial. Key recommendations include:

- **Structured Logging**: Log in machine-readable (JSON) format, with consistent fields (timestamp, level, component, call_id, event, message, duration, error_code, etc.).  Structured logs enable automated querying.  For example, use `structlog` or Python’s JSONFormatter to emit logs like `{"timestamp":"2026-08-18T15:23:10Z","level":"INFO","call_id":"abc123","event":"CALL_START","to":"+441632...","from":"+123456...","message":"Call initiated"}`.  As New Relic advises, structured JSON logs make automated analysis much easier.  

- **Metrics to Collect**: At a minimum, track:  
  - **Call counts**: total calls, successful calls, failed calls.  
  - **Connection Rate**: percentage of attempted calls that connected.  
  - **High Post-Dial Delay (PDD)**: calls where ringing was delayed beyond threshold.  
  - **Audio Quality**: jitter, packet loss, latency histograms for RTP streams (if measurable via Voice Insights or stats).  
  - **Who Hung Up**: percent where caller vs callee hung up.  
  - **API Failures**: errors from Twilio/SIP API calls, timeouts.  
  - **System resources**: CPU/memory usage under load.  
  - **Duration stats**: call length (mean, P50/P95).  

  These mirror Twilio Voice Insights metrics (e.g. connection rate, PDD, network issues).  Use a metrics system (Prometheus, CloudWatch) to record these counters/gauges.  

- **Distributed Tracing**: If the voice flow involves multiple services (webhook -> agent -> AI -> DB), use a tracing system (OpenTelemetry/Jaeger) to correlate spans. Tag traces with call_id and user/session id so logs and traces can be stitched.  

- **Alerts**: Define alerting rules, e.g.:  
  - **Call failure rate** above e.g. 5% triggers alert.  
  - **Call setup timeout**: if average PDD > 3s or connection rate drops below X%.  
  - **High error log count**: a sudden spike in ERROR-level logs in agent process (e.g. >10 in 1m).  
  - **Resource exhaustion**: if service CPU or memory exceeds threshold under expected load.  

  Each alert should include context (call_id samples, recent logs).  We suggest also sending alerts to an incident channel if any critical test fails or if monitoring shows anomalies.  

## Security and Secret Management  
- **Injection Safety**: Although voice inputs are mostly spoken, still sanitize any text used (e.g. user-provided names or messages) before using in DB queries or dynamic prompts, to prevent injection attacks.  
- **Authentication Bypass**: Test that SIP/TLS credentials cannot be spoofed; ensure any SIP credentials (SIP usernames, tokens) are stored securely (do not log them) and rotated. Use unit tests to verify that endpoints require valid tokens (mock expired tokens).  
- **Secrets Exposure**: Do not hard-code Twilio/SIP API keys; use environment variables or secret vault. In tests, ensure no secrets appear in logs or exceptions.  
- **Rate-limiting Security**: If there’s a public HTTP endpoint, ensure it’s protected against brute force (e.g. too many requests) by rate-limiting.  

## Test Harness and Mocking Strategies  
- **Framework**: Use `pytest` (Python) or an equivalent for unit tests. For HTTP endpoints, use a test client (e.g. Flask test client or FastAPI’s TestClient) to simulate requests. For SIP/Twilio interactions, stub out the HTTP client calls (e.g. using `responses` library or `unittest.mock` for Twilio REST SDK) or use Twilio’s built-in test credentials and magic numbers.  
- **Telephony Mocks**:  
  - **Twilio Test Mode**: Twilio provides special HTTP credentials and numbers that emulate call outcomes (e.g. `+15005550006` returns “no answer”). Use these in integration tests.  
  - **SIP Stubs**: Run a local dummy SIP server (e.g. from [ha-intratone/mock_asterisk README] or [SIPp](https://github.com/SIPp/pysipp)) that can be scripted to answer or hang up. Use pytest fixtures to start/stop these stubs during tests.  
  - **NLP/ASR Mocks**: If using an external speech service, mock its API to return predetermined transcriptions.  

- **Test Code Examples (Python)**: 
  ```python
  # Example unit test for phone validation
  import pytest
  from curago.call_utils import validate_phone

  @pytest.mark.parametrize("number,valid", [
      ("+441632960960", True),
      ("441632960960", False),
      ("ABC123", False),
  ])
  def test_validate_phone(number, valid):
      if valid:
          assert validate_phone(number) is True
      else:
          with pytest.raises(ValueError):
              validate_phone(number)

  # Example integration test with Twilio mock
  import responses
  @responses.activate
  def test_initiate_call_success(monkeypatch):
      responses.add(responses.POST, "https://api.twilio.com/2010-04-01/Accounts/ACxxx/Calls.json",
                    json={"sid": "CA123", "status": "queued"}, status=201)
      # Call the function that uses Twilio REST API
      call_sid = curago.voice.make_call("+441632960960")
      assert call_sid == "CA123"
      # ... further assertions ...
  ```
  These snippets illustrate unit tests and mocked integration tests; the project should include similar templates for each service.

## CI/CD Integration and Test Execution Plan  
Integrate tests into a continuous pipeline (e.g. GitHub Actions, GitLab CI, Jenkins) with stages:

```mermaid
flowchart TD
    A[Checkout Code] --> B[Install Dependencies & Lint]
    B --> C[Unit Tests (fast, mocks)]
    C --> D[Static Analysis / Security Scan]
    D --> E[Integration Tests (mocked)]
    E --> F[Build/Package Artifact]
    F --> G[Deploy to Staging]
    G --> H[Sanity End-to-End Tests (limited real calls)]
    H --> I[Manual Review / Gating]
    I --> J[Deploy to Production]
    style B fill:#e8f6ff,stroke:#333,stroke-width:2px
    style C fill:#e8f6ff,stroke:#333,stroke-width:2px
    style E fill:#fdebd0,stroke:#333,stroke-width:2px
    style H fill:#fadbd8,stroke:#333,stroke-width:2px
    style I fill:#fdebd0,stroke:#333,stroke-width:2px
```

- **Unit Tests Stage**: Run all unit tests on every commit (short runtime, mocks only) to catch immediate errors. Enforce code coverage thresholds (e.g. >80%).  
- **Integration Tests Stage**: After unit tests, run integration tests that simulate calls (can still use Twilio test mode or local SIPp server). These may take longer but should still be automated.  
- **End-to-End Staging**: Before production, deploy to a staging environment and execute a small set of end-to-end scenarios (e.g. place one real test call to a lab number) to validate readiness.  
- **Gating**: The pipeline should fail and block merges if any high-priority test fails. For lower-priority or long-running tests (e.g. full load test), consider a separate nightly pipeline or manual trigger.  
- **Reporting**: Test results should be reported (e.g. to console or CI UI), and if possible, broken down by category. Code coverage and lint issues should also be visible.  
- **Artifact and Deployment**: Build the deployable service artifact (Docker image or package) only after passing tests. Then deploy to the target environment with monitoring hooks.  

## Logging Format and Tracing Spans (Recommendation)  
Use a consistent JSON schema for logs. A recommended format (inspired by [New Relic]):  
```json
{
  "timestamp": "2026-08-18T18:22:34Z",
  "level": "INFO",
  "service": "voice-agent",
  "call_id": "CAabcdef123456",
  "event": "CALL_END",
  "duration_ms": 54321,
  "status": "completed",
  "to": "+441632960960",
  "from": "+1234987654",
  "error": null
}
```  
Key fields: `timestamp`, `level`, `service`/component, `call_id` (unique per call session), `event` (CALL_START, CALL_END, ERROR), and relevant context (phone numbers, duration, status, error code). Use a structured logging library (e.g. Python’s `structlog`) to emit JSON.  

For tracing, assign a **trace ID** per call (e.g. equal to call_id) that is included in logs and propagated to downstream service calls. Each processing step (e.g. HTTP request to NLP) should be a span. This lets you see, for a given call, the timeline of actions (answer, play prompt, ASR call, hang up).  

## Metrics and Alerting  
Collect metrics on-call events. In Prometheus-like format, examples:  
```
voice_call_total{result="success"} 100
voice_call_total{result="busy"} 5
voice_call_duration_seconds_sum{result="success"} 5000
voice_call_duration_seconds_count{result="success"} 100
```
Compute derived metrics: success rate, average duration, etc. 

Use Twilio Voice Insights metrics as a guide: monitor **Connection Rate** (successful calls / attempted) and **High PDD rate**. For instance, an alert: “if connection_rate < 90% over 5 min, trigger incident.” Similarly, track packet-loss and jitter from Voice SDK or media stats if available.

## Security and Rate-Limit Tests  
In addition to input sanitation mentioned above, include tests for:  
- **Brute-force/DOS**: If HTTP endpoints exist, simulate high-frequency requests (e.g. 100 req/s) to ensure rate limits or protections hold.  
- **Configuration Permutations**: Test with env vars toggled (e.g. debug mode on/off) to catch missing configuration. Use fixture files for different settings (dev, prod credentials).  

## Observability Tests (During-Call Checks)  
Implement logging during-call to capture key events: e.g. on each major step (call initiated, answered, prompt played, user responded, call ended), log with unique call_id. Tests should verify that logs are emitted in the correct order and that no sensitive info leaks. For example, an automated check could ingest the log stream and assert that for every `CALL_START` there is a corresponding `CALL_END` with a duration > 0.  

## Test Execution Plan Summary  
Schedule pre-call (unit) tests on every PR (fast, automate). Run integration/voice-flow tests on merge or nightly (to allow SIPp or Twilio test usage). Periodic load tests (e.g. weekly) can be manual or in a separate CI job (since they require more resources).  

Automated tests should generate pass/fail reports. Manual tests (e.g. actual real-call sanity checks) should be limited to a small sanctioned set due to cost.  

**Table: Test Types and Priorities**  

| Test Type          | Examples                                     | Priority | Runtime       | Approx. Cost (Mock) | Approx. Cost (Real Call) |
|--------------------|----------------------------------------------|----------|---------------|---------------------|-------------------------|
| **Unit**           | Phone validation, config parsing, logic      | High     | ~0.1s/test    | Very low (none)     | –                       |
| **Mock Integration** | Twilio API stubbed, simulated SIP flows    | High     | ~0.5s–5s      | Low (no call charges) | Moderate (Twilio fees ~\$0.01/call)  |
| **Voice Flow Tests** | Simulated calls with audio, DTMF          | High     | ~5–15s       | Low (if using test mode) | Higher (each call~\$0.01–\$0.10) |
| **Performance**    | SIPp concurrency load                        | Medium   | Minutes–hours | Moderate (server CPU) | Very High (if using toll calls) |
| **Security**       | Auth bypass, injection                      | High     | ~1s–10s/test | None                | –                       |
| **Observability**  | Metric correctness, alert firing            | Medium   | Continuous    | None                | –                       |
| **End-to-End**     | Full call on staging phone                  | Medium   | ~10s–1m      | Moderate (few calls) | Cost of each test call  |

Use mock/simulated tests whenever possible (cost column shows real calls are expensive). Real-call tests should be minimal (smoke tests), saving the bulk of validation for offline or simulated modes.

**Table: Priority by Category**  

| Category             | Priority | Notes                                     |
|----------------------|----------|-------------------------------------------|
| Input Validation     | High     | Early bugs, no cost to run                |
| Core Call Flows      | High     | Core functionality (use mocks)            |
| Error Handling       | High     | Prevent outages                           |
| Concurrency/Perf     | Medium   | Important for load but less frequent runs |
| Security             | High     | Always critical                           |
| Observability/Alerts | Medium   | Catch post-release issues early           |
| CI Integration       | High     | Automate gating                           |

These tables guide focusing effort: unit and integration tests get top priority (fast, automated), while full voice calls and performance tests are more limited (expensive/time-consuming).  

## Conclusion  
In summary, the CURAGO voice agent requires a *four-layer QA approach*:  
1. **Unit Tests & Mocks** for all functions and input validation (fast, no real calls).  
2. **Simulated In-Call Tests** (using SIP/VoIP test tools and Twilio test mode) for voice flow logic (to catch audio/ASR issues).  
3. **Observability Verification** to ensure logs/metrics/traces are generated and alerts fire on anomalies (leveraging Twilio Voice Insights metrics).  
4. **Controlled Live Call Checks** only as a final sanity check before production (minimised to save cost).  

The provided sample test cases, tables and diagrams should serve as a blueprint.  Following best practices and citing authoritative sources ensures the test plan is robust: structured logging, SIP testing steps, and telephony metrics anchor our recommendations. Careful CI integration and monitoring will help prevent expensive real-call errors and maintain the reliability of the voice agent in production.  

**Sources:** Authoritative guides on voice-agent testing and telephony best practices. (Official docs referenced where applicable.)