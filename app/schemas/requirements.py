from app.schemas.common import CamelModel


class StartGenerationBody(CamelModel):
    input_snapshot_id: str
    expected_input_revision: int
