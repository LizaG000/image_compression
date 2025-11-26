from src.usecase.base import Usecase
from dataclasses import dataclass
from src.library.ExpLieSVDSingleCodec import ExpLieSVDSingleCodec
from src.usecase.image.schemas import CompressSchema
from loguru import logger


@dataclass(slots=True, frozen=True, kw_only=True)
class DecompressUsecase(Usecase[CompressSchema, bytes]):

    async def __call__(self, data: CompressSchema) -> bytes:
        logger.info(23)
        exp = ExpLieSVDSingleCodec(data.h, data.rank, data.qbits)
        logger.info(23)
        return exp.decompress(data.img)
