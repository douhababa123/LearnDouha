"""
API 集成测试公共 fixtures
- 使用内存 SQLite，每次测试独立数据库
- 覆盖 get_db 依赖，确保隔离
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base

# ---------- 测试数据库 ----------
# 使用 StaticPool 保证所有连接共享同一个内存 SQLite 连接，表创建后对所有会话可见
@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # 导入所有模型，确保 Base 知道所有表
    from app.models import user, question, learning, story  # noqa
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    """每个测试函数独立的 TestClient + 内存 DB"""
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------- 通用辅助函数 ----------

def register_and_login(client, username, password, role, nickname):
    """注册 + 登录，返回 (token, user_id)"""
    client.post("/api/auth/register", json={
        "username": username,
        "password": password,
        "role": role,
        "nickname": nickname,
    })
    resp = client.post("/api/auth/token", data={
        "username": username,
        "password": password,
    })
    data = resp.json()
    return data["access_token"], data["user_id"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- 常用 fixtures ----------

@pytest.fixture
def parent_token(client):
    """注册家长并返回 (token, headers)"""
    token, uid = register_and_login(client, "parent_user", "pass123", "parent", "测试爸爸")
    return token, auth_header(token)


@pytest.fixture
def child_setup(client, parent_token):
    """家长已登录 → 创建一个孩子，返回 (child_id, parent_headers)"""
    token, headers = parent_token
    resp = client.post("/api/children/", json={"nickname": "小明", "grade": 2}, headers=headers)
    child_id = resp.json()["child_id"]
    return child_id, headers


@pytest.fixture
def questions_in_db(client, parent_token):
    """向题库中批量插入 20 道题，返回 parent_headers"""
    token, headers = parent_token
    items = [
        {"original_text": f"2{i} + 1{i} = ___"} for i in range(10)
    ] + [
        {"original_text": f"5{i} - 2{i} = ___"} for i in range(10)
    ]
    client.post("/api/questions/batch", json={"questions": items}, headers=headers)
    return headers
