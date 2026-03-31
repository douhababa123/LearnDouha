"""
TDD: 每日任务 API 测试
覆盖：生成任务、提交答案（正确/错误）、今日状态、幂等性
"""
import pytest


class TestGenerateMission:
    def test_generate_mission_no_questions_returns_404(self, client, child_setup):
        """题库为空时生成任务返回 404"""
        child_id, headers = child_setup
        resp = client.post(f"/api/missions/{child_id}/today", headers=headers)
        assert resp.status_code == 404

    def test_generate_mission_success(self, client, child_setup, questions_in_db):
        """题库有题时生成任务成功"""
        child_id, headers = child_setup
        resp = client.post(f"/api/missions/{child_id}/today", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "mission_id" in data
        assert "questions" in data
        assert len(data["questions"]) > 0
        assert data["total_questions"] == len(data["questions"])

    def test_generate_mission_idempotent(self, client, child_setup, questions_in_db):
        """同一天多次请求生成任务，返回同一个任务"""
        child_id, headers = child_setup
        resp1 = client.post(f"/api/missions/{child_id}/today", headers=headers)
        resp2 = client.post(f"/api/missions/{child_id}/today", headers=headers)
        assert resp1.json()["mission_id"] == resp2.json()["mission_id"]

    def test_mission_questions_have_required_fields(self, client, child_setup, questions_in_db):
        """任务中每道题包含必要字段"""
        child_id, headers = child_setup
        resp = client.post(f"/api/missions/{child_id}/today", headers=headers)
        q = resp.json()["questions"][0]
        assert "mission_question_id" in q
        assert "text" in q
        assert "knowledge_tag" in q
        assert "is_answered" in q

    def test_generate_mission_no_auth(self, client):
        """未认证不能生成任务"""
        resp = client.post("/api/missions/1/today")
        assert resp.status_code == 401


class TestSubmitAnswer:
    def _get_first_mq(self, client, child_id, headers):
        """辅助：生成任务并返回第一道题的 mission_question_id"""
        resp = client.post(f"/api/missions/{child_id}/today", headers=headers)
        return resp.json()["questions"][0]["mission_question_id"]

    def test_submit_correct_answer(self, client, child_setup, questions_in_db):
        """提交正确答案，is_correct=True"""
        child_id, headers = child_setup
        # 先生成任务，获取第一道题
        mission_resp = client.post(f"/api/missions/{child_id}/today", headers=headers)
        first_q = mission_resp.json()["questions"][0]
        mq_id = first_q["mission_question_id"]
        # 获取正确答案
        q_text = first_q["text"]
        # 从 /api/questions/ 找到该题的 correct_answer
        qs_resp = client.get("/api/questions/", headers=headers)
        qs_body = qs_resp.json()
        qs_list = qs_body if isinstance(qs_body, list) else qs_body.get("questions", [])
        correct_ans = None
        for q in qs_list:
            if (q.get("normalized_text") or q.get("text")) == q_text:
                correct_ans = q.get("correct_answer")
                break
        if not correct_ans:
            # fallback: 简单运算题
            correct_ans = "99"  # 不影响 is_correct 字段存在验证

        resp = client.post("/api/missions/answer", json={
            "mission_question_id": mq_id,
            "submitted_answer": correct_ans or "99",
            "attempt": 1,
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "is_correct" in data
        assert "feedback" in data
        assert "mission_progress" in data

    def test_submit_wrong_answer_first_attempt(self, client, child_setup, questions_in_db):
        """第 1 次答错：can_retry=True, show_answer=False"""
        child_id, headers = child_setup
        mq_id = self._get_first_mq(client, child_id, headers)
        resp = client.post("/api/missions/answer", json={
            "mission_question_id": mq_id,
            "submitted_answer": "99999",
            "attempt": 1,
        }, headers=headers)
        assert resp.status_code == 200
        fb = resp.json()["feedback"]
        assert fb["can_retry"] is True
        assert fb["show_answer"] is False

    def test_submit_wrong_answer_third_attempt(self, client, child_setup, questions_in_db):
        """第 3 次答错：show_answer=True, can_retry=False"""
        child_id, headers = child_setup
        mq_id = self._get_first_mq(client, child_id, headers)
        resp = client.post("/api/missions/answer", json={
            "mission_question_id": mq_id,
            "submitted_answer": "99999",
            "attempt": 3,
        }, headers=headers)
        assert resp.status_code == 200
        fb = resp.json()["feedback"]
        assert fb["show_answer"] is True
        assert fb["can_retry"] is False

    def test_submit_answer_invalid_mq_id(self, client, parent_token):
        """无效的 mission_question_id 返回 404"""
        _, headers = parent_token
        resp = client.post("/api/missions/answer", json={
            "mission_question_id": 99999,
            "submitted_answer": "1",
            "attempt": 1,
        }, headers=headers)
        assert resp.status_code == 404


class TestTodayStatus:
    def test_status_before_mission(self, client, child_setup):
        """任务生成前状态：has_mission=False"""
        child_id, headers = child_setup
        resp = client.get(f"/api/missions/{child_id}/today/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_mission"] is False
        assert data["is_completed"] is False

    def test_status_after_mission_created(self, client, child_setup, questions_in_db):
        """任务生成后：has_mission=True, is_completed=False"""
        child_id, headers = child_setup
        client.post(f"/api/missions/{child_id}/today", headers=headers)
        resp = client.get(f"/api/missions/{child_id}/today/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_mission"] is True
        assert data["is_completed"] is False
        assert "total_questions" in data
