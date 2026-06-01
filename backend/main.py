import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s — %(message)s")

from api.routes import router
from api.websocket_routes import ws_router
from auth.routes import router as auth_router
from database.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Sequre QKD Platform",
    description="BB84 Quantum Key Distribution simulation API.",
    version="0.1.0",
    lifespan=lifespan,
)

# SessionMiddleware is required by Authlib to persist the OAuth `state`
# parameter between the redirect-out and callback. The session is signed
# but not encrypted — we don't put anything sensitive in it.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-session-secret-change-me"),
    same_site="lax",
    https_only=os.getenv("COOKIE_SECURE", "false").lower() == "true",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(router)
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "sequre-backend"}
