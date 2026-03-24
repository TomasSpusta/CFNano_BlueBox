# Software Architecture Improvement Plan

This document proposes a practical, phased improvement roadmap for the current Python async state-machine app (RFID + GPIO buttons + LCD + HTTP API + Google Sheets logging).

## 1. Current-State Assessment

### Strengths
- Clear high-level flow with explicit states (`Init -> WaitingForCard -> VerifyUser -> VerifyReservation -> InReservation -> End`).
- Hardware integrations are encapsulated in dedicated modules (`rfid_reader.py`, `lcd_display.py`, button watcher).
- Use of `asyncio` enables non-blocking orchestration at architecture level.
- Domain models are small and easy to understand.

### Key Risks and Gaps
- Reliability risk: several runtime bugs and fragile error paths.
- Concurrency risk: blocking hardware I/O inside async flow.
- Maintainability risk: duplicated API/network/token logic and inconsistent patterns.
- Observability risk: `print()`-based logging with partial fallback.
- Quality risk: missing test suite and no CI gates.
- Operational risk: no graceful shutdown / lifecycle management.

## 2. Immediate Critical Fixes (Phase 0 - 1 to 2 days)

1. Fix hard runtime bugs.
- `logger.py`: `Path.write_text(..., append=True)` is invalid; replace with explicit append mode (`open('a')`) in a thread-safe helper.
- `states/offline_state.py`: references `context.api.check_connection()` which does not exist; either remove state or add a valid connectivity API.
- `model_classes.py`: `Reservation.warning_sent`, `ended_by_user`, `ended_by_time` are class attributes; convert to dataclass instance fields.
- `app_context.py`: `button_lock = asyncio.Lock()` at class definition time can bind to wrong event loop; move to instance initialization.

2. Prevent event-loop blocking.
- `rfid_reader.py`: wrap blocking `self.reader.read()` using `asyncio.to_thread`.
- Verify all hardware calls touching GPIO/LCD are either async-safe or wrapped.

3. Add defensive API timeout defaults.
- Define centralized aiohttp timeout config (connect/read/total).
- Apply request-level timeout and consistent exception handling.

4. Remove dead/duplicate module behavior.
- `button_handler.py` and `button_watcher.py` overlap; keep one implementation and delete/retire the other.

Acceptance criteria:
- App runs for >2h without deadlock.
- No `AttributeError` / loop-binding errors in logs.
- Card scanning remains responsive while network checks happen.

## 3. Foundation Refactor (Phase 1 - 3 to 5 days)

1. Introduce layered architecture.
- `domain/`: entities and pure business rules.
- `application/`: state machine orchestration/use-cases.
- `infrastructure/`: GPIO/LCD/RFID/API/Google Sheets adapters.
- `interfaces/` (optional): CLI/bootstrap/runtime wiring.

2. Normalize state transitions.
- Define explicit transition map and terminal fallback behavior.
- Standardize state contract: input context, returned next state, and error behavior.

3. Centralize configuration.
- Replace implicit `from config import config` coupling with typed settings object.
- Support env-based config with validation (e.g., `pydantic-settings` or dataclass + validation).
- Keep secrets out of repository and document required variables.

4. Unify API client behavior.
- Reuse one shared `aiohttp.ClientSession` per app lifecycle.
- Add typed API responses and normalized error objects.
- Deduplicate token fetch flow (`APIClient.fetch_token` vs `networking.fetch_token`).

Acceptance criteria:
- Single dependency direction (state logic does not import hardware modules directly).
- One token-refresh implementation.
- Config validation fails fast on startup with clear message.

## 4. Reliability and Resilience (Phase 2 - 3 to 4 days)

1. Build robust online/offline strategy.
- Create a `ConnectivityService` with backoff and jitter.
- Separate connectivity state from UI rendering side effects.
- Avoid two independent offline loops (`network_monitor` + `wait_until_online`) racing screen output.

2. Introduce operation policies.
- Retry policy for transient HTTP failures (idempotent calls only).
- Circuit breaker for persistent backend failures.
- Graceful degradation mode (local queue of critical events while offline).

3. Improve shutdown/startup lifecycle.
- Add structured startup sequence and health checks.
- Handle SIGTERM/SIGINT: cancel tasks, cleanup GPIO/LCD, flush pending logs.

Acceptance criteria:
- Controlled behavior during network flap tests.
- Clean shutdown without hung tasks or orphan GPIO handlers.

## 5. Observability and Logging (Phase 3 - 2 to 3 days)

1. Replace `print()` with structured logging.
- Use Python `logging` (JSON format preferred).
- Include correlation fields: `state`, `card_id` hash, `reservation_id`, `request_id`.

2. Improve logger subsystem.
- Decouple business events from Google Sheets writer via queue.
- Non-blocking buffered writes with retry and fallback file sink.
- Add clear log event schema versioning.

3. Add metrics.
- Track: API latency, API error counts by endpoint, state transition counts, RFID read latency, button events.

Acceptance criteria:
- Operational timeline can be reconstructed from logs.
- Failures are diagnosable without reproducing locally.

## 6. Security Hardening (Phase 4 - 1 to 2 days)

1. Secret handling.
- Store API keys/service-account path via environment or secret manager.
- Ensure token file permissions are restrictive.

2. Data handling.
- Avoid logging sensitive user fields directly (`full_name`, raw token).
- Add minimal PII policy in docs.

3. Dependency and supply-chain checks.
- Add vulnerability scanning in CI (`pip-audit` or equivalent).
- Pin and regularly update dependencies.

Acceptance criteria:
- No credentials in code/config files.
- Basic security checklist passes in CI.

## 7. Test Strategy and Quality Gates (Phase 5 - 4 to 6 days)

1. Unit tests.
- `token_handler` expiration logic.
- state transitions for success/failure/offline paths.
- reservation warnings and extension boundary conditions.

2. Integration tests.
- Mock API with `aioresponses`.
- Simulate RFID/button inputs with adapter fakes.

3. Hardware-in-the-loop smoke tests.
- Minimal scripted checks for LCD write, RFID read, button press events.

4. CI pipeline.
- `ruff` + `black` + `mypy` + `pytest` as required checks.

Acceptance criteria:
- >70% coverage on core state/application modules.
- PRs blocked when lint/types/tests fail.

## 8. Developer Experience and Documentation (Phase 6 - 1 to 2 days)

1. Add missing docs.
- `README.md`: architecture, setup, run commands, env vars.
- `docs/architecture.md`: component diagram and state transition diagram.
- `docs/operations.md`: deployment, restart, troubleshooting, logs.

2. Standardize project tooling.
- Add `pyproject.toml` and tool configs.
- Add `Makefile`/task runner for local commands (`lint`, `test`, `run`).

3. Track architectural decisions.
- Add ADRs for major choices (state machine model, logging backend, retry policy).

Acceptance criteria:
- New engineer can run and debug app within 30 minutes.

## 9. Proposed Execution Order

1. Phase 0: critical bug and blocking-I/O fixes.
2. Phase 1: architecture/config/API consolidation.
3. Phase 2: resilience and lifecycle controls.
4. Phase 3: observability uplift.
5. Phase 4: security hardening.
6. Phase 5: tests + CI quality gates.
7. Phase 6: docs and DX completion.

## 10. Backlog of Specific Code-Level Changes

- [ ] Fix fallback local logger append implementation in `logger.py`.
- [ ] Convert `Token` to dataclass and `Reservation` flags to instance fields.
- [ ] Move `button_lock` to per-context initialization.
- [ ] Replace blocking RFID read with threaded call.
- [ ] Create shared `ClientSession` lifecycle in `main.py` and inject into `APIClient`.
- [ ] Remove duplicate `fetch_token` implementation and consolidate in one service.
- [ ] Replace `print` with structured logger.
- [ ] Add startup config validator.
- [ ] Add graceful shutdown hooks and task cancellation handling.
- [ ] Add first wave of unit tests for token + state transitions.

## 11. Notes/Assumptions

- The `config/` directory is gitignored, so this plan assumes runtime config exists outside repository.
- Hardware dependencies (GPIO/LCD/RFID) require interface abstraction for full CI testability.
- Google Sheets logging can remain, but should be isolated from synchronous app flow.
