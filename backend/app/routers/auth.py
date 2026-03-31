"""
认证路由 - 登录、注册、Token
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.database import get_db
from app.models.user import User, Parent, Child, UserRole

router = APIRouter()

# JWT 配置
SECRET_KEY = "learnhaha-math-adventure-secret-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# --- Schemas ---
class UserRegister(BaseModel):
    username: str
    password: str
    role: str  # "parent" or "child"
    nickname: str


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int


class TokenData(BaseModel):
    username: Optional[str] = None


# --- 工具函数 ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# --- 路由 ---
@router.post("/register", summary="注册账号")
def register(data: UserRegister, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    if data.role not in ("parent", "child"):
        raise HTTPException(status_code=400, detail="角色必须为 parent 或 child")

    user = User(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        role=UserRole(data.role),
    )
    db.add(user)
    db.flush()

    if data.role == "parent":
        profile = Parent(user_id=user.id, nickname=data.nickname)
        db.add(profile)
    else:
        profile = Child(user_id=user.id, nickname=data.nickname, parent_id=None)
        db.add(profile)

    db.commit()
    db.refresh(user)
    return {"message": "注册成功", "user_id": user.id, "role": user.role}


@router.post("/token", response_model=Token, summary="登录获取Token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
    )


@router.get("/me", summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
    }
