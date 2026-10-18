from app.schemas.common import CamelModel


class CreateRequestBody(CamelModel):
    title: str
    legacy_reference_id: str


class InputPayload(CamelModel):
    title: str
    text: str = ""
    html: str = ""
    desired_due_date: str | None = None
    attachment_ids: list[str] = []


class PatchRequestBody(CamelModel):
    expected_request_revision: int
    input: InputPayload | None = None
    working_requirement_document_id: str | None = None
    expected_input_revision: int | None = None
