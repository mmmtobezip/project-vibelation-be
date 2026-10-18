from app.schemas.common import CamelModel


class ConfirmBody(CamelModel):
    requirement_document_id: str
    expected_input_revision: int
    expected_request_revision: int
