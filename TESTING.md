# 검증 가이드 — 설계서 대비 확인 방법

이 문서는 `docs/backend-design_v01.md`(아키텍처)와 `docs/api_interface_v06.md`
(API/Mock 계약, 특히 §19~§21)를 기준으로, 지금 구현이 그 설계와 실제로 일치하는지
사용자가 직접 확인할 수 있는 방법을 정리한 것입니다. 세 단계로 구성됩니다:
자동 테스트 → 수동 curl 재현 → 설계서 항목별 체크리스트.

## 0. 사전 준비

```bash
cd project-vibelation-be
. .venv/bin/activate   # 없으면: python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]" python-multipart   # asyncpg가 로컬에서 빌드 실패하면 DB 관련 줄은 무시해도 됨(이번 단계는 DB 미사용)
```

## 1. 자동 테스트 (가장 빠른 확인 방법)

```bash
python -m pytest -v
```

10개 테스트, 파일별로 설계서의 어느 항목을 검증하는지 매핑하면:

| 파일 | 검증 대상 | 설계서 위치 |
|---|---|---|
| `tests/test_golden_path.py` | REQ→FILE→MD→CONF→ANA→RPT→REG 전체 흐름 + MOCK-01/03/05 | `backend-design_v01.md` §15 "필수 테스트" 1번, `api_interface_v06.md` §19.5 |
| `tests/test_idempotency.py` | 같은 Idempotency-Key·같은 본문 → 같은 리소스 / 다른 본문 → 409 | `api_interface_v06.md` §2 "멱등성과 재시도" |
| `tests/test_error_cases.py` | VERSION_CONFLICT, STALE_INPUT, JOB_ALREADY_RUNNING, ATTACHMENT_NOT_READY, DOCUMENT_MISMATCH, REVIEW_CHECKS_REQUIRED, NOT_FOUND | `api_interface_v06.md` §13 "공통 오류 계약", §3 "버전·확정·경합 규칙" |

전부 통과해야 "정상"입니다. 특정 설계 규칙이 의심스러우면 해당 테스트 함수 하나만
`pytest -v -k test_이름`으로 떼어서 보면 어떤 입력/응답으로 그 규칙을 검증하는지
바로 보입니다.

## 2. 실제 서버로 수동 재현 (curl)

pytest는 ASGITransport(인메모리 호출)라서 "진짜 HTTP"가 아닙니다. 네트워크
레이어까지 포함해 확인하려면:

```bash
uvicorn app.main:app --reload --port 8000
```

다른 터미널에서:

```bash
BASE=http://127.0.0.1:8000/api ./scripts/smoke_test.sh
```

이 스크립트는 `tests/test_golden_path.py`와 동일한 흐름을 curl로 그대로
재현하면서, 각 단계마다 `api_interface_v06.md`의 몇 절에 해당하는지 라벨을
찍고 실제 JSON 응답을 보여줍니다. 중간에 실패하면 `set -e`로 그 자리에서
멈추므로 어느 API에서 깨졌는지 바로 압니다.

개별 API만 하나씩 찔러보고 싶다면 `/docs`(Swagger UI)에서 바로 "Try it out"으로
호출할 수 있습니다 — 34개 라우트가 전부 뜨고, 이번에 구현한 28개는 실제 응답을,
`legacy-systems`/`source-packages`(SYS/SRC, §20)는 여전히 `501 NOT_IMPLEMENTED`를
반환합니다. OpenAPI 스펙만 전수 확인하려면:

```bash
curl -s http://127.0.0.1:8000/openapi.json | python3 -c "
import json, sys
paths = json.load(sys.stdin)['paths']
for path, methods in sorted(paths.items()):
    print(path, list(methods.keys()))
"
```

## 3. 설계서 항목별 체크리스트

### 3.1 공통 규약 (`api_interface_v06.md` §2~§3)

| 항목 | 확인 방법 | 기대 결과 |
|---|---|---|
| 응답이 camelCase | 아무 GET 응답 확인 | `requestRevision`, `inputSnapshotId` 등 camelCase |
| 단건은 객체, 목록은 `{items,nextCursor}` | `GET /api/requests` vs `GET /api/requests/{id}` | 목록만 `items` 배열 |
| expectedRequestRevision 불일치 → 409 | `test_error_cases.py::test_version_conflict_on_stale_patch` 또는 smoke script 2번째 호출에서 revision을 틀리게 | `VERSION_CONFLICT` + `details.currentRequestRevision` |
| Idempotency-Key 재사용 | `test_idempotency.py` 2개 테스트 | 같은 본문=같은 ID, 다른 본문=409 `IDEMPOTENCY_CONFLICT` |
| 같은 kind 중복 Job 차단 | `test_job_already_running_blocks_concurrent_generation` | 두 번째 호출 409 `JOB_ALREADY_RUNNING` + `details.jobId` |

### 3.2 MD 단일 입력 계약 (§19)

| 항목 | 확인 방법 | 기대 결과 |
|---|---|---|
| ANA-01 본문엔 MD 파일 하나(+§21 ZIP) | `app/api/routes/analyses.py` 시그니처, smoke script "ANA-01" 단계 | `file` 필수, `sourceFiles`/`sourceManifest`는 선택 |
| 업로드 MD가 확정 스냅샷과 다르면 거부 | `test_document_mismatch_on_tampered_markdown` | 409 `DOCUMENT_MISMATCH` |
| 이전 버전 MD도 선택·확정 가능 | REQ-04로 `workingRequirementDocumentId`를 과거 문서 id로 설정 후 CONF-01 | 확정 성공 (문서의 `inputRevision`이 현재와 달라도 통과) — 직접 손으로 한 번 눌러보는 걸 권장, 현재 자동 테스트엔 이 케이스가 없음 |

### 3.3 §21 override (MOCK-01/ANA-01 멀티파트, ANA-03 응답 모양)

| 항목 | 확인 방법 | 기대 결과 |
|---|---|---|
| MOCK-01이 `sourceFiles[]`+`sourceManifest` 받는지 | `tests/test_golden_path.py`의 mock 플로우, 또는 `app/api/routes/mocks.py` | 필드명이 camelCase(`requirementDocumentId`, `legacyVersion`, `sourceFiles`, `sourceManifest`) |
| ANA-03 응답이 `impacts/totalDays/durationDays/bufferDays` 단순 포맷 | `GET /api/analysis-results/{id}` 직접 호출 | `resources/evidence/estimate` 같은 구버전 필드는 없어야 함 |

### 3.4 Mock Agent 동작 (`backend-design_v01.md` §9, Mock 단계 대체)

| 항목 | 확인 방법 | 기대 결과 |
|---|---|---|
| Job이 즉시 완료되지 않고 queued→running→succeeded를 거치는지 | smoke script의 "poll" 라인들 | 첫 응답 `queued`, 900ms 전 폴링은 `running`, 이후 `succeeded` |
| 결과가 `mocks/*.json` 템플릿에서 왔는지 | `mocks/requirement-document.json` 등 수정 후 서버 재시작 → 같은 플로우 재실행 | 변경한 문구가 새로 생성되는 MD/분석/리포트에 반영됨 |

### 3.5 범위 밖 — 실패해야 "정상"인 것들

| 항목 | 확인 방법 | 기대 결과 |
|---|---|---|
| SYS-01~03, SRC-01~03 (§20) | `curl -X POST http://127.0.0.1:8000/api/legacy-systems -d '{}'` | `501 NOT_IMPLEMENTED` — 이번 범위에 포함 안 함 |
| 서버 재시작 후 데이터 보존 | 서버 재시작 후 이전 request id로 `GET /api/requests/{id}` | `404` — DB가 아니라 인메모리라 재시작하면 날아감(README에 명시) |
| 실제 OIDC 인증 | 헤더 없이 아무 요청 | 그냥 통과함 — `DEV_AUTH=true`라 고정 identity(`user-01`) 사용 중, 운영 인증 아님 |
| multipart 엔드포인트(FILE-02/MOCK-01/ANA-01)의 Idempotency-Key | 같은 파일로 두 번 업로드 | 멱등 처리 안 됨(알려진 제한, JSON 본문 5개 생성 API에만 적용했음) |

## 4. FE와 실제로 맞춰보기 (참고, 이번 범위 밖)

지금 FE(`project-vibelation`)의 `src/services/requirements.ts`는 v0.8 옛 계약이라
위 서버에 그대로 붙지 않습니다. FE 어댑터를 고치지 않고도 눈으로 비교하고
싶다면, 이 문서 2번 섹션의 curl 응답 모양을 FE `src/domain/types.ts`의 타입과
나란히 놓고 필드명을 대조하는 정도까지만 지금 할 수 있는 확인입니다.
