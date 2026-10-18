from app.schemas.common import CamelModel


class ReviewChecks(CamelModel):
    scope_reviewed: bool
    estimate_reviewed: bool


class RegisterReviewBody(CamelModel):
    request_id: str
    confirmation_id: str
    analysis_result_id: str
    report_id: str
    review_checks: ReviewChecks
