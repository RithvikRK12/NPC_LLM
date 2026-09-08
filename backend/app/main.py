from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config.settings import get_settings
from app.database.init_db import initialize_database
from app.database.seed import seed_world
from app.database.session import SessionLocal


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_title)

    origins = settings.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if origins == ["*"] else origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup() -> None:
        initialize_database()
        with SessionLocal() as db:
            seed_world(db)

    app.include_router(api_router)
    return app


app = create_app()