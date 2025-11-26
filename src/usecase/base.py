from abc import abstractmethod
from typing import Protocol
from typing import TypeVar

TInputDTO = TypeVar('TInputDTO', contravariant=True)
TOutputDTO = TypeVar('TOutputDTO', covariant=True)


class Usecase(Protocol[TInputDTO, TOutputDTO]):
    @abstractmethod
    async def __call__(self, data: TInputDTO) -> TOutputDTO:
        """Абстрактный метод для реализации бизнес - логикию"""
