from fastapi import FastAPI
from dishka.integrations.fastapi import setup_dishka
from src.main.config import config
from src.presentation.fastapi.setup import setup_routes
from src.main.container import container
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=config.api.project_name
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # разрешаем запросы с любых доменов
    allow_credentials=True,
    allow_methods=["*"],       # разрешаем все методы
    allow_headers=["*"],       # разрешаем все заголовки
)

setup_routes(app, config)
setup_dishka(container, app)
