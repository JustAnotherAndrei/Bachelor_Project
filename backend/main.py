"""
Q-Shield Backend — FastAPI application entry point.

Mounts REST routes and WebSocket routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.websocket_routes import ws_router

app = FastAPI(
    title="Q-Shield QKD Platform",
    description="BB84 Quantum Key Distribution simulation and hardware execution API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "q-shield-backend"}
