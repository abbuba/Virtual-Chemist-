from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from redis.exceptions import RedisError
from app.database import init_db
from app.seed import seed_database
from app.routers.auth_router import router as auth_router
from app.routers.chem_router import router as chem_router
import os

app = FastAPI(title="The Virtual Chemist API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
seed_database(verbose=False)

app.include_router(auth_router)
app.include_router(chem_router)


@app.exception_handler(RedisError)
async def redis_unavailable(request: Request, exc: RedisError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Login service (Redis) is not running. Please start Redis and try again."},
    )

# Mount static files
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(static_dir, "index.html"))
