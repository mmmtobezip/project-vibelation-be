"""Agent client Protocol + Mock implementation.

Internal contract per backend-design_v01.md §9:
  POST /internal/v1/tasks
  GET  /internal/v1/tasks/by-operation/{operationId}
  GET  /internal/v1/tasks/{taskId}
  GET  /internal/v1/tasks/{taskId}/result

kind: requirement | systemMock | analysis | report | attachmentExtraction

Mock 응답 모양은 레포 루트 mocks/*.json 템플릿을 그대로 따른다. analysis의
경우 api_interface_v06.md §21(최신 override)을 기준으로
impacts/totalDays/durationDays/bufferDays 단순 포맷을 쓴다 — 이는 FE의
src/domain/types.ts Analysis/Impact 타입과 1:1 대응한다.

실제 결정적 응답 생성 로직(fixture 로드 + 자리표시자 치환)은 다음 단계에서
구현한다. 지금은 Protocol 형태만 고정해 라우터/서비스가 import할 수 있게 한다.
"""

from typing import Protocol


class AgentClient(Protocol):
    async def submit(self, operation_id: str, kind: str, basis: dict, input: dict) -> dict: ...

    async def get_status(self, task_id: str) -> dict: ...

    async def get_result(self, task_id: str) -> dict: ...


class MockAgentClient:
    """TODO: load backend-root mocks/*.json fixtures and return deterministic results."""

    async def submit(self, operation_id: str, kind: str, basis: dict, input: dict) -> dict:
        raise NotImplementedError

    async def get_status(self, task_id: str) -> dict:
        raise NotImplementedError

    async def get_result(self, task_id: str) -> dict:
        raise NotImplementedError
