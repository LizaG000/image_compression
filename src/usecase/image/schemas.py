from pydantic import BaseModel, ConfigDict
from io import BytesIO
from fastapi import UploadFile

class CompressSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    img: BytesIO
    h: float
    rank: int
    qbits: int
