from fastapi import FastAPI
from dishka.integrations.fastapi import setup_dishka
from src.main.config import config
from src.presentation.fastapi.setup import setup_routes
from src.main.container import container

app = FastAPI(
    title=config.api.project_name
)

setup_routes(app, config)
setup_dishka(container, app)
