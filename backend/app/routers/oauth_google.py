"""OAuth Google — requer GOOGLE_CLIENT_ID/SECRET e redirect URI no console Google."""
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.oauth_account import OAuthAccount
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security import create_access_token, hash_password

router = APIRouter(prefix="/auth/google", tags=["oauth"])
settings = get_settings()


@router.get("/start")
async def google_start(request: Request):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(501, "OAuth Google não configurado (defina GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET).")
    state = secrets.token_urlsafe(32)
    request.session["oauth_google_state"] = state
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.oauth_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/callback")
async def google_callback(request: Request, code: str | None = None, state: str | None = None, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(400, "Código ausente")
    expected = request.session.get("oauth_google_state")
    if not state or state != expected:
        raise HTTPException(400, "State inválido")
    request.session.pop("oauth_google_state", None)

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    if token_res.status_code != 200:
        raise HTTPException(400, "Falha ao trocar código por token")
    tokens = token_res.json()
    access = tokens.get("access_token")
    async with httpx.AsyncClient() as client:
        ui = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access}"},
        )
    if ui.status_code != 200:
        raise HTTPException(400, "Falha ao obter perfil")
    profile = ui.json()
    email = profile.get("email")
    sub = profile.get("sub")
    name = profile.get("name") or email
    if not email or not sub:
        raise HTTPException(400, "Perfil incompleto")

    repo = UserRepository(db)
    existing_oauth = repo.get_oauth("google", sub)
    if existing_oauth:
        user = repo.get_by_id(existing_oauth.user_id)
    else:
        user_by_email = repo.get_by_email(email)
        if user_by_email:
            user = user_by_email
            db.add(OAuthAccount(user_id=user.id, provider="google", sub=sub))
        else:
            user = repo.create_oauth_user(
                email=email,
                full_name=name,
                provider="google",
                sub=sub,
                hashed_password=hash_password(secrets.token_urlsafe(32)),
            )
    db.commit()
    jwt_token = create_access_token(str(user.id))
    target = f"{settings.frontend_url}/oauth-callback?token={jwt_token}"
    return RedirectResponse(target)
