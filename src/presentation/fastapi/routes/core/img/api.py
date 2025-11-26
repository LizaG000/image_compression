from dishka.integrations.fastapi import DishkaRoute
from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, UploadFile, File, Query, Response
from fastapi import status
from src.usecase.image.compress import CompressUsecase
from src.usecase.image.decompress import DecompressUsecase
from io import BytesIO
from src.usecase.image.schemas import CompressSchema
ROUTER = APIRouter(route_class=DishkaRoute)

@ROUTER.post('/compress', status_code=status.HTTP_200_OK)
async def compress(
    usecase: FromDishka[CompressUsecase],
    file: UploadFile = File(...),  # Исправлено: File вместо Query
    h: float = Query(...),
    rank: int = Query(...),
    qbits: int = Query(...)
) -> Response:
    image_bytes = await file.read()
    result =  await usecase(CompressSchema(
        img = BytesIO(image_bytes),
        h=h,
        rank=rank,
        qbits=qbits
    ))
    return Response(
        content=result,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": "attachment; filename=compressed.exp"
        })


@ROUTER.post('/decompress', status_code=status.HTTP_200_OK)
async def decompress(
    usecase: FromDishka[DecompressUsecase],
    file: UploadFile = File(...),  # Исправлено: File вместо Query
    h: float = Query(...),
    rank: int = Query(...),
    qbits: int = Query(...)
) -> Response:

    image_bytes = await file.read()
    result =  await usecase(CompressSchema(
        img = BytesIO(image_bytes),
        h=h,
        rank=rank,
        qbits=qbits
    ))
    return Response(
        content=result,
        media_type="image/jpeg",
        headers={
            "Content-Disposition": "attachment; filename=decompressed.jpg"
        })