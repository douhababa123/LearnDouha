"""
TDD: 孩子管理 API 测试
覆盖：创建孩子、列出孩子、打卡记录、权限校验
"""
import pytest
from tests.conftest import register_and_login, auth_header


class TestCreateChild:
    def test_parent_can_create_child(self, client, parent_token):
        """家长成功创建孩子"""
        _, headers = parent_token
        resp = client.post("/api/children/", json={
            "nickname": "小明",
            "grade": 2,
            "avatar": "squirrel",
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["nickname"] == "小明"
        assert data["grade"] == 2
        assert "child_id" in data

    def test_create_child_default_grade(self, client, parent_token):
        """创建孩子，grade 默认为 2"""
        _, headers = parent_token
        resp = client.post("/api/children/", json={"nickname": "小红"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["grade"] == 2

    def test_non_parent_cannot_create_child(self, client):
        """孩子角色不能创建孩子（403）"""
        token, uid = register_and_login(client, "child_acc", "pw123", "child", "小孩")
        resp = client.post("/api/children/", json={"nickname": "弟弟"}, headers=auth_header(token))
        assert resp.status_code == 403

    def test_create_child_no_auth(self, client):
        """未认证不能创建孩子（401）"""
        resp = client.post("/api/children/", json={"nickname": "匿名"})
        assert resp.status_code == 401


class TestListChildren:
    def test_list_children_empty(self, client, parent_token):
        """新注册的家长，孩子列表为空"""
        _, headers = parent_token
        resp = client.get("/api/children/", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_children_after_create(self, client, parent_token):
        """创建 2 个孩子后列表有 2 条"""
        _, headers = parent_token
        client.post("/api/children/", json={"nickname": "A"}, headers=headers)
        client.post("/api/children/", json={"nickname": "B"}, headers=headers)
        resp = client.get("/api/children/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_parents_cannot_see_each_others_children(self, client):
        """两个家长各自只看到自己的孩子"""
        token1, _ = register_and_login(client, "p1", "pw1", "parent", "爸爸1")
        token2, _ = register_and_login(client, "p2", "pw2", "parent", "爸爸2")
        h1, h2 = auth_header(token1), auth_header(token2)

        client.post("/api/children/", json={"nickname": "P1孩子"}, headers=h1)

        resp2 = client.get("/api/children/", headers=h2)
        assert resp2.json() == []


class TestStreak:
    def test_initial_streak_is_zero(self, client, child_setup):
        """新建孩子的打卡记录为 0"""
        child_id, headers = child_setup
        resp = client.get(f"/api/children/{child_id}/streak", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_streak"] == 0
        assert data["max_streak"] == 0
        assert data["total_checkins"] == 0
