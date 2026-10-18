from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for request bodies: external JSON is camelCase, Python stays snake_case.

    Responses are returned as plain dicts built with camelCase keys directly by
    the services layer (see app/services/common.py) — no response models needed
    for this Mock stage.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
