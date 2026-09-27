from fastapi import APIRouter

from app.api.v1 import health

# Every v1 router is attached here, which is what makes main.py unaware of how
# many feature routers exist. Adding a feature never means editing main.py.
api_router = APIRouter()
api_router.include_router(health.router)
