"""
TDD: 认证 API 测试
覆盖：注册、登录、获取当前用户、错误处理
"""
import pytest


class TestRegister:
    def test_register_parent_success(self, client):
        """家长注册成功"""
        resp = client.post("/api/auth/register", json={
            "username": "papa01",
            "password": "secret123",
            "role": "parent",
            "nickname": "测试爸爸",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "注册成功"
        assert "user_id" in data
        assert data["role"] == "parent"

    def test_register_child_success(self, client):
        """孩子注册成功"""
        resp = client.post("/api/auth/register", json={
            "username": "kid01",
            "password": "abc123",
            "role": "child",
            "nickname": "小红",
        })
        assert resp.status_code == 200
        assert resp.json()["role"] == "child"

    def test_register_duplicate_username(self, client):
        """重复用户名返回 400"""
        payload = {"username": "dup_user", "password": "pw", "role": "parent", "nickname": "N"}
        client.post("/api/auth/register", json=payload)
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 400
        assert "已存在" in resp.json()["detail"]

    def test_register_invalid_role(self, client):
        """非法角色返回 400"""
        resp = client.post("/api/auth/register", json={
            "username": "user_x",
            "password": "pw",
            "role": "admin",
            "nickname": "N",
        })
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self, client):
        """正确账密登录，返回 JWT token"""
        client.post("/api/auth/register", json={
            "username": "login_user",
            "password": "mypassword",
            "role": "parent",
            "nickname": "爸爸",
        })
        resp = client.post("/api/auth/token", data={
            "username": "login_user",
            "password": "mypassword",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "parent"
        assert isinstance(data["user_id"], int)

    def test_login_wrong_password(self, client):
        """密码错误返回 401"""
        client.post("/api/auth/register", json={
            "username": "user_pw",
            "password": "correct_pw",
            "role": "parent",
            "nickname": "N",
        })
        resp = client.post("/api/auth/token", data={
            "username": "user_pw",
            "password": "wrong_pw",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        """不存在的用户返回 401"""
        resp = client.post("/api/auth/token", data={
            "username": "ghost_user",
            "password": "anything",
        })
        assert resp.status_code == 401


class TestGetMe:
    def test_get_me_success(self, client, parent_token):
        """持有有效 token 可获取自身信息"""
        token, headers = parent_token
        resp = client.get("/api/auth/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "parent_user"
        assert data["role"] == "parent"

    def test_get_me_no_token(self, client):
        """无 token 访问 /me 返回 401"""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client):
        """伪造 token 返回 401"""
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer fake.token.here"})
        assert resp.status_code == 401
