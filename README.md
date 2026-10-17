# VIBELATION Backend (scaffold)

`project-vibelation`(FE)과 분리된 별도 레포. REST API 서버 + Mock Agent 기반 스캐폴드.

## 기준 문서

로컬 전용(`docs/`, git에는 올라가지 않음 — `.gitignore` 참고):

- `docs/backend-design_v01.md` — 아키텍처(FastAPI/SQLAlchemy/Job-dispatcher)
- `docs/api_interface_v06.md`(v1.6) — API/Mock 계약. **§19(MD 단일 입력)가 기본,
  §21(2026-10-18 최신 개정)이 MOCK-01/ANA-01 multipart와 ANA-03 응답 포맷을 덮어씀**

## API 범위 (34개, 라우터는 현재 전부 501 자리표시자)

| 영역 | API | 파일 |
|---|---|---|
| 요청/초안 | REQ-01~04, REF-01 | `app/api/routes/requests.py` |
| 첨부 | FILE-01~03 | `app/api/routes/files.py` |
| 요구사항 MD | MD-01~05 | `app/api/routes/requirements.py` |
| 예상 화면 Mock | MOCK-01·03·05 (02/04/06 제외) | `app/api/routes/mocks.py` |
| MD 확정 | CONF-01~03 | `app/api/routes/confirmations.py` |
| 레거시 분석 | ANA-01~03 | `app/api/routes/analyses.py` |
| 리포트 | RPT-01~03 | `app/api/routes/reports.py` |
| 등록·이력 | REG-01~03 | `app/api/routes/history.py` |
| 레거시 시스템 ZIP | SYS-01~03 | `app/api/routes/legacy_systems.py` |
| 소스 패키지 ZIP | SRC-01~03 | `app/api/routes/source_packages.py` |

## §21 override 요약

- `MOCK-01`, `ANA-01`의 multipart 본문은 `file`(MD) + 반복 `sourceFiles`(ZIP bytes) +
  `sourceManifest`([{index,id,name,role,sha256,sizeBytes}]) + `legacyVersion`.
- `ANA-03` 응답은 단순 포맷: `impacts/totalDays/durationDays/bufferDays`
  (각 impact: `id,type,name,path,current,proposed,reason,days`) — 이는 FE
  `src/domain/types.ts`의 `Analysis`/`Impact`와 1:1 대응하므로 어댑터가 필요 없다.

## 구현 순서 (backend-design_v01.md §15 기반)

1. FastAPI 기반·설정·DB·오류·개발 인증
2. 요청·스냅샷·파일·추출·MD Job (+ SRC-01~03 ZIP 업로드 처리 포함)
3. 이전 MD 선택·확정
4. 단일 MD 분석 + Agent HTTP (§21 multipart 기준)
5. 리포트·등록·이력
6. 선택 HTML 생성·검증·FE 연동
7. 운영 인증·장애·동시성

현재는 1단계 이전의 **스캐폴드 뼈대만** 있는 상태 — 라우터는 등록되어 있지만 전부
`NotImplementedError`(HTTP 501)를 반환한다.

## 로컬 실행

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
# http://127.0.0.1:8000/health/live
# http://127.0.0.1:8000/docs
```
