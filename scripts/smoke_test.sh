#!/usr/bin/env bash
# Manual curl walk-through of the golden path, annotated with the
# api_interface_v06.md section each call maps to. Mirrors
# tests/test_golden_path.py but against a real running server so you can
# eyeball every response. Requires: server already running
# (`uvicorn app.main:app --port 8000`), curl, python3.
#
# Usage: BASE=http://127.0.0.1:8000/api ./scripts/smoke_test.sh
set -euo pipefail
BASE="${BASE:-http://127.0.0.1:8000/api}"

field() { python3 -c "import json,sys; d=json.load(sys.stdin); print(d$1)"; }
step() { printf '\n\033[1;36m== %s ==\033[0m\n' "$1"; }

step "REQ-01 요청 생성 (api_interface_v06.md §5)"
CREATE=$(curl -s -X POST "$BASE/requests" \
  -H 'Content-Type: application/json' \
  -d '{"title":"다운로드 센터 개선","legacyReferenceId":"legacy-01"}')
echo "$CREATE" | python3 -m json.tool
REQUEST_ID=$(echo "$CREATE" | field "['id']")
REV=$(echo "$CREATE" | field "['requestRevision']")
[ "$REV" = "1" ] && echo "OK requestRevision=1"

step "REQ-04 입력 저장 (§19.1, inputRevision 증가 확인)"
PATCHED=$(curl -s -X PATCH "$BASE/requests/$REQUEST_ID" \
  -H 'Content-Type: application/json' \
  -d '{"expectedRequestRevision":1,"input":{"title":"다운로드 센터 개선","text":"최대 10개 파일을 선택하고 싶습니다.","html":"","desiredDueDate":null,"attachmentIds":[]}}')
echo "$PATCHED" | python3 -m json.tool
SNAPSHOT_ID=$(echo "$PATCHED" | field "['inputSnapshotId']")
INPUT_REV=$(echo "$PATCHED" | field "['inputRevision']")
REQ_REV=$(echo "$PATCHED" | field "['requestRevision']")
[ "$INPUT_REV" = "2" ] && echo "OK inputRevision=2"

step "MD-01 요구사항 생성 시작 (§8, §19.1)"
GEN=$(curl -s -X POST "$BASE/requests/$REQUEST_ID/requirement-generations" \
  -H 'Content-Type: application/json' \
  -d "{\"inputSnapshotId\":\"$SNAPSHOT_ID\",\"expectedInputRevision\":$INPUT_REV}")
echo "$GEN" | python3 -m json.tool
JOB_ID=$(echo "$GEN" | field "['id']")

step "MD-03 생성 진행 폴링 (§7 공통 Job, pollAfterMs 참고)"
for i in $(seq 1 10); do
  GEN=$(curl -s "$BASE/requests/$REQUEST_ID/requirement-generations/$JOB_ID")
  STATUS=$(echo "$GEN" | field "['status']")
  echo "poll $i: status=$STATUS"
  [ "$STATUS" = "succeeded" ] && break
  sleep 0.3
done
echo "$GEN" | python3 -m json.tool
DOCUMENT_ID=$(echo "$GEN" | field "['result']['id']")

step "MD-05 MD 상세 조회"
DOC=$(curl -s "$BASE/requests/$REQUEST_ID/requirement-documents/$DOCUMENT_ID")
echo "$DOC" | python3 -m json.tool

step "REQ-04 선택 MD 저장 (workingRequirementDocumentId)"
SELECTED=$(curl -s -X PATCH "$BASE/requests/$REQUEST_ID" \
  -H 'Content-Type: application/json' \
  -d "{\"expectedRequestRevision\":$REQ_REV,\"workingRequirementDocumentId\":\"$DOCUMENT_ID\"}")
echo "$SELECTED" | python3 -m json.tool
SEL_INPUT_REV=$(echo "$SELECTED" | field "['inputRevision']")
SEL_REQ_REV=$(echo "$SELECTED" | field "['requestRevision']")

step "CONF-01 MD 확정 (§19.3, 201 기대)"
CONFIRM=$(curl -s -i -X POST "$BASE/requests/$REQUEST_ID/requirement-confirmations" \
  -H 'Content-Type: application/json' \
  -d "{\"requirementDocumentId\":\"$DOCUMENT_ID\",\"expectedInputRevision\":$SEL_INPUT_REV,\"expectedRequestRevision\":$SEL_REQ_REV}")
echo "$CONFIRM" | head -1
CONFIRMATION=$(echo "$CONFIRM" | sed -n '/^{/,$p')
echo "$CONFIRMATION" | python3 -m json.tool
CONFIRMATION_ID=$(echo "$CONFIRMATION" | field "['id']")

step "ANA-01 분석 실행 — 확정 MD 파일 하나만 전송 (§19.4, §21 override)"
# Write markdown straight to a file (not through a bash variable) so we don't
# lose the trailing newline bash command substitution strips — that bytes-for-
# bytes match is exactly what DOCUMENT_MISMATCH enforces.
echo "$CONFIRMATION" | python3 -c "
import json, sys
open('/tmp/requirements.md', 'w', encoding='utf-8').write(json.load(sys.stdin)['documentSnapshot']['markdown'])
"
ANALYSIS_JOB=$(curl -s -X POST \
  "$BASE/requests/$REQUEST_ID/requirement-confirmations/$CONFIRMATION_ID/analysis-jobs" \
  -F "file=@/tmp/requirements.md;type=text/markdown")
echo "$ANALYSIS_JOB" | python3 -m json.tool
ANALYSIS_JOB_ID=$(echo "$ANALYSIS_JOB" | field "['id']")

step "ANA-02 분석 진행 폴링"
for i in $(seq 1 10); do
  ANALYSIS_JOB=$(curl -s "$BASE/analysis-jobs/$ANALYSIS_JOB_ID")
  STATUS=$(echo "$ANALYSIS_JOB" | field "['status']")
  echo "poll $i: status=$STATUS"
  [ "$STATUS" = "succeeded" ] && break
  sleep 0.3
done
ANALYSIS_ID=$(echo "$ANALYSIS_JOB" | field "['result']['id']")

step "ANA-03 영향도 결과 (§21: impacts/totalDays/durationDays/bufferDays)"
ANALYSIS=$(curl -s "$BASE/analysis-results/$ANALYSIS_ID")
echo "$ANALYSIS" | python3 -m json.tool

step "RPT-01 리포트 생성"
REPORT_JOB=$(curl -s -X POST "$BASE/review-reports" \
  -H 'Content-Type: application/json' \
  -d "{\"requestId\":\"$REQUEST_ID\",\"confirmationId\":\"$CONFIRMATION_ID\",\"analysisResultId\":\"$ANALYSIS_ID\"}")
REPORT_JOB_ID=$(echo "$REPORT_JOB" | field "['id']")

step "RPT-02 리포트 진행 폴링"
for i in $(seq 1 10); do
  REPORT_JOB=$(curl -s "$BASE/report-jobs/$REPORT_JOB_ID")
  STATUS=$(echo "$REPORT_JOB" | field "['status']")
  echo "poll $i: status=$STATUS"
  [ "$STATUS" = "succeeded" ] && break
  sleep 0.3
done
REPORT_ID=$(echo "$REPORT_JOB" | field "['result']['id']")

step "RPT-03 리포트 상세"
curl -s "$BASE/review-reports/$REPORT_ID" | python3 -m json.tool

step "REG-01 검토 등록 (201 기대)"
REGISTER=$(curl -s -i -X POST "$BASE/review-registrations" \
  -H 'Content-Type: application/json' \
  -d "{\"requestId\":\"$REQUEST_ID\",\"confirmationId\":\"$CONFIRMATION_ID\",\"analysisResultId\":\"$ANALYSIS_ID\",\"reportId\":\"$REPORT_ID\",\"reviewChecks\":{\"scopeReviewed\":true,\"estimateReviewed\":true}}")
echo "$REGISTER" | head -1
REGISTRATION=$(echo "$REGISTER" | sed -n '/^{/,$p')
echo "$REGISTRATION" | python3 -m json.tool
REGISTRATION_ID=$(echo "$REGISTRATION" | field "['id']")

step "REG-02 등록 이력 검색"
curl -s "$BASE/review-registrations" | python3 -m json.tool

step "REG-03 등록 당시 상세"
curl -s "$BASE/review-registrations/$REGISTRATION_ID" | python3 -m json.tool

printf '\n\033[1;32mGolden path smoke test complete.\033[0m\n'
