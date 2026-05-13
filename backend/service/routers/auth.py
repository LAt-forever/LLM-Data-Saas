from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

from service.config import settings
from service.security import verify_password
from service.session import session_store

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    username: str


@router.post("/login", response_model=UserOut)
def login(req: LoginRequest, response: Response) -> UserOut:
    if req.username != settings.admin_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not verify_password(req.password, settings.admin_password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    session_id = session_store.create_session(req.username)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=24 * 60 * 60,  # 24h
        secure=False,  # Set True in production with HTTPS
        path="/",
    )
    return UserOut(username=req.username)


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, bool]:
    session_id = request.cookies.get("session_id")
    if session_id:
        session_store.delete_session(session_id)
    response.delete_cookie(key="session_id", path="/")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(request: Request) -> UserOut:
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    data = session_store.get_session(session_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )
    return UserOut(username=data.username)
