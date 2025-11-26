from src.usecase.base import Usecase
from dataclasses import dataclass
from src.library.ExpLieSVDSingleCodec import ExpLieSVDSingleCodec
from src.usecase.image.schemas import CompressSchema


@dataclass(slots=True, frozen=True, kw_only=True)
class CompressUsecase(Usecase[CompressSchema, bytes]):

    async def __call__(self, data: CompressSchema) -> bytes:
        exp = ExpLieSVDSingleCodec(data.h, data.rank, data.qbits)
        return exp.compress(data.img)
