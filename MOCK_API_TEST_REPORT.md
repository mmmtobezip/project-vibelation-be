# 시스템 적용 예상 화면(MOCK) API 테스트 결과서

- 작성일: 2026-10-18
- 대상 커밋: `bc60b90` (+ 이 보고서 작성 중 발견된 결함 수정 1건, 아래 4절)
- 테스트 환경: Python 3.13.3, FastAPI 0.115.14, Pydantic 2.14.1, uvicorn 0.32.1, httpx 0.27.2 (`project-vibelation-be/.venv`)
- 서버: `uvicorn app.main:app --port 8090` (실제 HTTP, ASGITransport 아님)
- 기준 문서: `api_interface_v06.md` §4(API 목록), §19.1~19.2(MD 단일 입력 계약), §21(ZIP 동시 전송 override)
- 목적: Agent 서버 미연결 상태에서 BE가 `MOCK-01/03/05`를 FE 대신 호출했을 때 **임의(Mock) 데이터로 정상 동작**하는지 실제 요청/응답을 근거로 검증하고, `MOCK-02/04/06`이 설계서대로 "현재 계약에서 제외"되어 있는지 확인.

## 1. 요약 결론

| API | 설계서 상태 | 실제 구현 | 테스트 결과 |
|---|---|---|---|
| MOCK-01 (예상 화면 생성 시작) | §21 override로 현재 계약에 포함 | 구현됨 (`app/api/routes/mocks.py`) | **PASS** — 정상 케이스 3종, 에러 케이스 3종 전부 기대대로 동작 |
| MOCK-03 (생성 진행 확인) | 현재 계약에 포함 | 구현됨 | **PASS** — queued→running→succeeded 전이 확인 |
| MOCK-05 (최신 예상 화면 조회) | 현재 계약에 포함 (단수 조회로 변경) | 구현됨 | **PASS** — 생성 전 404, 생성 후 200 모두 확인 |
| MOCK-02 (생성 이력 목록) | §19.1에서 "사용하지 않음" | 라우트 없음 | 설계대로 **미제공** — 단, 405(404 아님)로 응답, 2절 참고 |
| MOCK-04 (버전 목록) | §19.1에서 "사용하지 않음" | 라우트 없음 | 설계대로 **미제공** (404) |
| MOCK-06 (Preview 세션) | §19.1에서 "사용하지 않음" | 라우트 없음 | 설계대로 **미제공** (404) |

**테스트 중 실제 결함 1건 발견 → 즉시 수정함** (4절 참고): `MOCK-01`에 `JOB_ALREADY_RUNNING` 동시성 가드가 빠져 있었음. 수정 후 재검증 완료, 회귀 테스트(`tests/test_error_cases.py::test_job_already_running_blocks_concurrent_mock_generation`) 추가.

**알려진 제한(2차 검증 시 참고):** MOCK-01은 multipart라서 `Idempotency-Key`가 아직 적용되지 않음 — 같은 키로 재호출해도 새 Job이 생성됨 (3절 "참고 5" 증거 참조). JSON 본문 생성 API 5개(REQ-01/MD-01/CONF-01/RPT-01/REG-01)만 적용되어 있음.

## 2. 사전 준비 (MOCK-01에 필요한 선행 데이터)

MOCK-01은 "선택된 요구사항 MD"가 있어야 호출 가능하므로, 아래 순서로 실제 요청을 먼저 만들었다 (각 단계 자체는 이전 골든패스 테스트에서 이미 검증된 영역이라 응답 요약만 기록):

1. `POST /api/requests` → `{"id":"req-41a4337a23c0", "requestRevision":1, ...}`
2. `PATCH /api/requests/{id}` (입력 저장) → `inputRevision:2, inputSnapshotId:"input-d552d8425fcc"`
3. `POST /api/requests/{id}/requirement-generations` → Job 생성, 폴링 후 `succeeded`, `result.id = "md-0ad2403b3a7a"`
4. `PATCH /api/requests/{id}` (`workingRequirementDocumentId` 선택) → `requestRevision:3`

이 문서의 MOCK 테스트는 전부 `requestId=req-41a4337a23c0`, `documentId=md-0ad2403b3a7a` 기준이다.

## 3. MOCK-01/03/05 — 실제 Request/Response 근거

### 3.1 MOCK-05를 Mock 생성 **전**에 호출 — 404 기대

```
GET /api/requests/req-41a4337a23c0/system-mock
```
```
HTTP/1.1 404 Not Found
content-type: application/json

{"detail":{"error":{"code":"NOT_FOUND","message":"선택 MD의 예상 화면이 아직 없습니다.","retryable":false,"fieldErrors":[],"details":{}}}}
```
→ **PASS**. "생성 전엔 조회 실패"라는 §19.1 요구를 만족.

### 3.2 MOCK-01 정상 요청 — file + sourceFiles[] + sourceManifest (§21 override)

```
POST /api/requests/req-41a4337a23c0/system-mock-generations
Idempotency-Key: report-mock-01
Content-Type: multipart/form-data; boundary=...

-- 필드 --
file              = requirements_for_mock.md (text/markdown, 323 bytes, 실제 MD-05 markdown)
requirementDocumentId = md-0ad2403b3a7a
legacyVersion     = DEMO-2026.10
sourceFiles[0]    = fake_source_frontend.zip
sourceFiles[1]    = fake_source_backend.zip
sourceManifest    = [{"index":0,"id":"src-1","name":"frontend.zip","role":"frontend","sha256":"deadbeef","sizeBytes":42},
                      {"index":1,"id":"src-2","name":"backend.zip","role":"backend","sha256":"cafebabe","sizeBytes":57}]
```
```
HTTP/1.1 202 Accepted
content-type: application/json

{"id":"job-0c9be87cdde0","requestId":"req-41a4337a23c0","kind":"systemMock","status":"queued",
 "generationNumber":2,"basis":{"requirementDocumentId":"md-0ad2403b3a7a","legacyVersion":"DEMO-2026.10"},
 "result":null,"error":null,"createdAt":"2026-10-18T05:16:35.943Z","startedAt":null,"finishedAt":null,"pollAfterMs":500}
```
→ **PASS**. camelCase 필드명(`requirementDocumentId`, `legacyVersion`, `sourceFiles`, `sourceManifest`)이 실제로 바인딩됨 — 이전 세션에서 `Form(alias=...)` → `Annotated[..., Form(alias=...)]`로 바꾼 수정이 유효함을 재확인.

### 3.3 MOCK-03 폴링 — queued → succeeded 전이

```
GET /api/requests/req-41a4337a23c0/system-mock-generations/job-0c9be87cdde0
```
1차 폴링(이미 900ms 경과 후 호출됨):
```
HTTP/1.1 200 OK
{"id":"job-0c9be87cdde0", ..., "status":"succeeded","generationNumber":2,
 "result":{"type":"systemMock","id":"screen-0be0993e5cf6"},
 "startedAt":"2026-10-18T05:16:35.982Z","finishedAt":"2026-10-18T05:16:47.428Z","pollAfterMs":0}
```
→ **PASS**. `result.type="systemMock"` + `id`로 산출물 참조 제공, `pollAfterMs:0`으로 폴링 종료 신호 정상.

### 3.4 MOCK-05를 Mock 생성 **후**에 호출 — 200 + HTML

```
GET /api/requests/req-41a4337a23c0/system-mock
```
```
HTTP/1.1 200 OK
{"id":"screen-0be0993e5cf6","requestId":"req-41a4337a23c0","requirementDocumentId":"md-0ad2403b3a7a",
 "legacyVersion":"DEMO-2026.10",
 "html":"<!doctype html><html>...<h1>시스템 적용 예상 화면 (Mock)</h1><p>Mock Agent가 생성한 단독 실행 HTML 자리표시자입니다. 외부 통신은 CSP로 차단됩니다.</p>...</html>",
 "formatVersion":"system-mock-v1","createdAt":"2026-10-18T05:16:47.428Z"}
```
→ **PASS**. `mocks/system-mock.json` 템플릿의 `Content-Security-Policy` 헤더 메타태그가 그대로 포함되어 있음 — §19.2 "독립 실행 HTML + CSP" 요구 충족. (주의: 업로드한 `file`/`sourceFiles` 내용은 렌더링에 반영되지 않는다 — Mock 단계라 고정 템플릿만 반환. Agent 연결 후에는 실제 코드/요구사항을 반영해야 함.)

### 3.5 에러 케이스 1 — sourceFiles 개수 ≠ sourceManifest 길이

```
POST .../system-mock-generations  (sourceFiles 1개, sourceManifest 2개 항목)
```
```
HTTP/1.1 400 Bad Request
{"detail":{"error":{"code":"INVALID_REQUEST","message":"sourceFiles 개수와 sourceManifest 길이가 다릅니다.",...}}}
```
→ **PASS**.

### 3.6 에러 케이스 2 — 존재하지 않는 requirementDocumentId

```
POST .../system-mock-generations  (requirementDocumentId=md-does-not-exist)
```
```
HTTP/1.1 400 Bad Request
{"detail":{"error":{"code":"INVALID_REQUEST","message":"같은 요청의 요구사항 문서가 아닙니다.",...}}}
```
→ **PASS**.

### 3.7 참고 — 동일 Idempotency-Key 재전송 (알려진 제한)

같은 `Idempotency-Key: report-mock-01`로 MOCK-01을 다시 호출하면:
```
HTTP/1.1 202 Accepted
{"id":"job-97b9a222b2a9", ..., "generationNumber":3, ...}
```
→ **새 Job이 또 생성됨** (멱등 응답 재사용이 아님). JSON 바디 생성 API 5개에만 Idempotency-Key를 적용했고 multipart 3개(FILE-02/MOCK-01/ANA-01)는 아직 미적용이라는 `TESTING.md` 3.5절의 "알려진 제한사항"이 실제로 재현됨. 버그가 아니라 **의도적으로 범위 밖으로 남긴 부분**.

## 4. 테스트 중 발견한 결함과 수정

**발견**: `MOCK-01`은 같은 요청에 대해 `systemMock` Job이 이미 `queued`/`running` 상태여도 새 Job을 또 만들어줬다. `requirements_service.start_generation`과 `analyses_service.start_analysis`는 둘 다 이 가드가 있는데 `mocks_service.start_mock_generation`에만 빠져 있었음 — `backend-design_v01.md` §10 "한 요청·kind의 queued/running Job은 ... 하나만 허용" 위반.

**수정**: `app/services/mocks_service.py`의 `start_mock_generation`에 동일한 가드 추가.

```python
existing = [j for j in store.jobs_for(request_id, "systemMock") if j["status"] in ("queued", "running")]
if existing:
    raise errors.job_already_running(existing[0]["id"])
```

**수정 후 재검증** (새 요청으로 연속 2회 즉시 호출):
```
--- 1차 ---
HTTP/1.1 202 Accepted
{"id":"job-dd8d185811ad", "status":"queued", "generationNumber":1, ...}

--- 2차 (같은 요청, 즉시 재호출) ---
HTTP/1.1 409 Conflict
{"detail":{"error":{"code":"JOB_ALREADY_RUNNING","message":"같은 종류의 작업이 이미 진행 중입니다.",
 "details":{"jobId":"job-dd8d185811ad"}}}}
```
→ 기대대로 두 번째 호출이 차단됨. 회귀 테스트 `tests/test_error_cases.py::test_job_already_running_blocks_concurrent_mock_generation` 추가, 전체 pytest 11개 통과 확인.

## 5. 범위 밖 확인 — MOCK-02/04/06

설계서 §19.1: *"MOCK-02/04의 사용자용 버전 목록 및 MOCK-06 Preview 세션은 이번 HTML 반환 계약에서 사용하지 않는다."* 실제로 라우트가 전혀 등록되어 있지 않음을 확인:

| API | 호출 | 실제 응답 | 비고 |
|---|---|---|---|
| MOCK-02 | `GET /api/requests/{id}/system-mock-generations` | **405 Method Not Allowed** `{"detail":"Method Not Allowed"}`, `Allow: POST` | 같은 경로에 MOCK-01의 `POST`가 등록돼 있어서 404가 아니라 405가 남 — 경로 자체는 "존재"하지만 메서드가 없다는 의미. 2차 검증 시 "404일 것"으로 기대하면 안 됨. |
| MOCK-04 | `GET /api/requests/{id}/system-mocks` | **404 Not Found** `{"detail":"Not Found"}` | 경로 자체가 등록 안 됨. FastAPI 기본 404(공통 오류 envelope 아님 — `error.code` 없음). |
| MOCK-06 | `POST /api/requests/{id}/system-mocks/{mockId}/preview-sessions` | **404 Not Found** `{"detail":"Not Found"}` | 동일. |

→ 설계서 의도(이 3개는 "제공 안 함")는 지켜졌지만, **MOCK-02는 404가 아니라 405**라는 점은 FE가 "엔드포인트 없음"을 판별하는 로직을 짤 때 알아둬야 할 실제 동작 차이다.

## 6. 자동화 테스트 (회귀 방지용)

```bash
cd project-vibelation-be && . .venv/bin/activate && python -m pytest -v
```
```
tests/test_error_cases.py::test_job_already_running_blocks_concurrent_mock_generation PASSED
tests/test_error_cases.py::test_version_conflict_on_stale_patch PASSED
tests/test_error_cases.py::test_stale_input_on_generation_with_wrong_revision PASSED
tests/test_error_cases.py::test_job_already_running_blocks_concurrent_generation PASSED
tests/test_error_cases.py::test_attachment_not_ready_rejects_unknown_attachment_id PASSED
tests/test_error_cases.py::test_document_mismatch_on_tampered_markdown PASSED
tests/test_error_cases.py::test_review_checks_required_when_not_both_true PASSED
tests/test_error_cases.py::test_not_found_for_unknown_request PASSED
tests/test_golden_path.py::test_golden_path PASSED
tests/test_idempotency.py::test_same_key_same_body_returns_same_resource PASSED
tests/test_idempotency.py::test_same_key_different_body_conflicts PASSED
============================== 11 passed in 9.60s ==============================
```

## 7. 2차 검증 방법 (사용자 재현용)

이 보고서의 모든 호출을 직접 재현하려면:

```bash
cd project-vibelation-be && . .venv/bin/activate
uvicorn app.main:app --port 8090 &
BASE=http://127.0.0.1:8090/api

# 1) 선행 데이터 만들기 (2절과 동일한 흐름) — 또는 scripts/smoke_test.sh의 앞부분을 그대로 사용
# 2) MOCK-01 정상 호출
curl -s -i -X POST "$BASE/requests/{requestId}/system-mock-generations" \
  -F "file=@requirements.md;type=text/markdown" \
  -F "requirementDocumentId={documentId}" \
  -F "legacyVersion=DEMO-2026.10" \
  -F "sourceFiles=@frontend.zip;type=application/zip" \
  -F "sourceFiles=@backend.zip;type=application/zip" \
  -F 'sourceManifest=[{"index":0,"id":"src-1","name":"frontend.zip","role":"frontend","sha256":"...","sizeBytes":1}]'

# 3) MOCK-03 폴링
curl -s "$BASE/requests/{requestId}/system-mock-generations/{jobId}"

# 4) MOCK-05 조회
curl -s "$BASE/requests/{requestId}/system-mock"

# 5) 범위 밖 확인
curl -s -i "$BASE/requests/{requestId}/system-mock-generations"   # MOCK-02 → 405 기대
curl -s -i "$BASE/requests/{requestId}/system-mocks"               # MOCK-04 → 404 기대
curl -s -i -X POST "$BASE/requests/{requestId}/system-mocks/{mockId}/preview-sessions"  # MOCK-06 → 404 기대
```

또는 자동화 버전: `pytest -v -k mock` (대소문자 무관, `test_golden_path`와 새 회귀 테스트가 걸린다).

## 8. 체크리스트 (2차 검증자용)

- [ ] MOCK-01이 camelCase 필드(`requirementDocumentId`, `legacyVersion`, `sourceFiles`, `sourceManifest`)를 정확히 받는지 재확인
- [ ] MOCK-03 폴링이 900ms 전/후로 `running`/`succeeded`를 구분하는지 재확인 (`agent_client.RUNNING_THRESHOLD_MS`)
- [ ] MOCK-05가 "선택된 MD" 기준으로만 응답하는지 — 다른 MD를 선택한 뒤 다시 조회하면 404가 나는지 확인 (이번 보고서에는 미포함, 추가 검증 권장)
- [ ] MOCK-02/04/06 응답 코드(405/404/404)가 FE 에러 처리 로직과 충돌하지 않는지 확인
- [ ] multipart Idempotency-Key 미적용이 실제 FE 연동 시 문제가 되는지 판단 (중복 클릭 방지 등)
