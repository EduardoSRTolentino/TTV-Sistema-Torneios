"""
TTV-Torneios — API FastAPI.
Fase 1: MVP com JWT, CRUD, chaveamento mata-mata.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import Base, engine, ensure_registration_extra_columns, ensure_tournament_extra_columns
from app.routers import admin_audit, auth, oauth_google, payments, ranking, reports, system_settings, tournaments, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ttv")

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.2.0")

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Erro não tratado: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})


@app.get("/")
def root():
    """Raiz da API (evita 404 ao abrir só a porta no navegador)."""
    return {
        "service": "ttv-torneios",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "ttv-torneios"}


app.include_router(auth.router)
app.include_router(oauth_google.router)
app.include_router(users.router)
app.include_router(system_settings.router)
app.include_router(tournaments.router)
app.include_router(ranking.router)
app.include_router(reports.router)
app.include_router(payments.router)
app.include_router(admin_audit.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    ensure_tournament_extra_columns()
    ensure_registration_extra_columns()
    logger.info("Tabelas verificadas/criadas.")
