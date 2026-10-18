from app.schemas.common import CamelModel


class StartReportBody(CamelModel):
    request_id: str
    confirmation_id: str
    analysis_result_id: str
