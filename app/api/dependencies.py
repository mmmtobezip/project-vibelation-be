"""DB session / identity dependency stubs.

Real implementations land with the DB layer in a later phase (see
backend-design_v01.md §15 단계 1-2). For now these exist so routers
have a stable import target.
"""

from collections.abc import AsyncIterator


async def get_db_session() -> AsyncIterator[None]:
    raise NotImplementedError("DB session dependency not wired yet")


async def get_current_identity() -> None:
    raise NotImplementedError("Auth dependency not wired yet")
