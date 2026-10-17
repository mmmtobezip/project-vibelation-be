# Mock Agent fixtures

`MockAgentClient`(`app/integrations/agent_client.py`, 아직 구현 전)가 읽을 결정적 응답
템플릿. FE의 `src/mocks/README.md` 관행(자리표시자 `{{...}}` + 템플릿 치환)을 그대로
따른다.

| 파일 | kind | 비고 |
|---|---|---|
| `requirement-document.json` | requirement | MD 생성 결과 markdown 템플릿 |
| `system-mock.json` | systemMock | 단독 실행 HTML (api_interface_v06.md §19.2) |
| `analysis-result.json` | analysis | §21 단순 포맷: impacts/totalDays/durationDays/bufferDays |
| `review-report.json` | report | 최종 검토 리포트 markdown 템플릿 |

실제 로드/치환 로직은 다음 단계(`agent_client.py`의 `MockAgentClient`)에서 구현한다.
