# Mock Agent fixtures

`MockAgentClient`(`app/integrations/agent_client.py`, 아직 구현 전)가 읽을 결정적 응답
템플릿. FE의 `src/mocks/README.md` 관행(자리표시자 `{{...}}` + 템플릿 치환)을 그대로
따른다.

| 파일 | kind | 비고 | 자리표시자 |
|---|---|---|---|
| `requirement-document.json` | requirement | MD 생성 결과 markdown 템플릿 | `{{generationNumber}}{{title}}{{inputRevision}}{{text}}{{html}}{{attachments}}` |
| `system-mock.json` | systemMock | 단독 실행 HTML (api_interface_v06.md §19.2) | `{{title}}{{legacyVersion}}{{requirementDocumentId}}` |
| `analysis-result.json` | analysis | §21 단순 포맷: impacts/totalDays/durationDays/bufferDays | 각 impact의 문자열 필드(name/path/current/proposed/reason)에 `{{title}}{{legacyVersion}}` |
| `review-report.json` | report | 최종 검토 리포트 markdown 템플릿 | `{{title}}{{version}}{{legacyVersion}}{{requirements}}{{impacts}}` |

`system-mock.json`/`analysis-result.json`은 숫자 필드(`days`/`totalDays`/`durationDays`/`bufferDays`)는 고정이고 문자열 필드만 요청별로 치환된다 — 실제 산정 로직이 아니라 "같은 입력은 같은 결과, 다른 입력은 눈에 보이게 다른 결과"를 보여주는 수준이다. 더 큰 변화(레거시 시스템별로 완전히 다른 impacts 구성 등)가 필요하면 파일을 여러 개로 나누고 `legacyReferenceId`로 선택하는 방식을 검토한다.

실제 로드/치환 로직은 `app/integrations/agent_client.py`의 `render_*` 함수들.
