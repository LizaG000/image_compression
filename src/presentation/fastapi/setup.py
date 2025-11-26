from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from fastapi import FastAPI
from src.config import Config
from src.presentation.fastapi.routes.core.setup import setup_core_router
from src.presentation.fastapi.exception_handlers import setup_exception_handlers

def setup_routes(app: FastAPI, config: Config) -> None:
    router = APIRouter(prefix='/api', route_class=DishkaRoute)
    router.include_router(router=setup_core_router())

    app.include_router(router)
    setup_exception_handlers(app=app)
    
