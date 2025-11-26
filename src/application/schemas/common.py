from pydantic import AliasGenerator
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import alias_generators


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(serialization_alias=alias_generators.to_camel),
        from_attributes=True,
        arbitrary_types_allowed=True,
    )
