from starlette import status
from src.infra.postgres.tables import BaseDBModel

class BaseError(Exception):
    def __init__(
            self,
            message='Произошла неизвестная ошибка.',
            status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> None:
        self.status_code = status_code
        self.message = message
    
    def __str__(self) -> str:
        return self.message

class InvalidCredentialsError(BaseError):
    def __init__(self,
                 message: str='Неверный логин или пароль.',
                 status_code = status.HTTP_401_UNAUTHORIZED):
        super().__init__(message, status_code)

class DatabaseCreateError(BaseError):
    def __init__(
        self,
        table: BaseDBModel,
        status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY,
    ):
        super().__init__(f"Ошибка при создании записи в модель: {table.__tablename__}", status_code)

class DatabaseUpdateError(BaseError):
    def __init__(
        self,
        table: BaseDBModel,
        status_code: int = status.HTTP_409_CONFLICT,
    ):
        super().__init__(f"Ошибка при обновлении записи в моделе: {table.__tablename__}", status_code)

class DatabaseDeleteError(BaseError):
    def __init__(
        self,
        table: BaseDBModel,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(f"Ошибка при удалении записи в моделе: {table.__tablename__}", status_code)

class NotFoundError(BaseError):
    def __init__(
        self,
        table: BaseDBModel,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        super().__init__(f"В {table.__tablename__} запись не найдена", status_code)
