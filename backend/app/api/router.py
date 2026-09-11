from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.memory import router as memory_router
from app.api.routes.npc import router as npc_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(npc_router)
api_router.include_router(memory_router)
from app.api.routes.world import router as world_router
api_router.include_router(world_router)

from app.api.routes.inventory import router as inventory_router
api_router.include_router(inventory_router)

from app.api.routes.quests import router as quests_router
api_router.include_router(quests_router)
