"""
TDD: 报告 API 测试
覆盖：今日总览、错题列表、薄弱点、周报
"""
import pytest


class TestOverview:
    def test_overview_with_no_mission(self, client, child_setup):
        """没有任务时，总览返回默认值"""
        child_id, headers = child_setup
        resp = client.get(f"/api/reports/{child_id}/overview", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_completed"] is False
        assert data["completed_questions"] == 0
        assert data["accuracy_rate"] == 0.0
        assert data["current_streak"] == 0

    def test_overview_after_mission_created(self, client, child_setup, questions_in_db):
        """生成任务后，total_questions > 0"""
        child_id, headers = child_setup
        client.post(f"/api/missions/{child_id}/today", headers=headers)
        resp = client.get(f"/api/reports/{child_id}/overview", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_questions"] > 0

    def test_overview_no_auth(self, client):
        """未认证不能访问报告"""
        resp = client.get("/api/reports/1/overview")
        assert resp.status_code == 401


class TestWrongQuestions:
    def test_wrong_questions_initially_empty(self, client, child_setup):
        """初始错题列表为空"""
        child_id, headers = child_setup
        resp = client.get(f"/api/reports/{child_id}/wrong_questions", headers=headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_wrong_questions_after_wrong_answer(self, client, child_setup, questions_in_db):
        """答错题后，错题列表出现该题"""
        child_id, headers = child_setup
        mission = client.post(f"/api/missions/{child_id}/today", headers=headers).json()
        mq_id = mission["questions"][0]["mission_question_id"]

        client.post("/api/missions/answer", json={
            "mission_question_id": mq_id,
            "submitted_answer": "99999",
            "attempt": 1,
        }, headers=headers)

        resp = client.get(f"/api/reports/{child_id}/wrong_questions", headers=headers)
        assert resp.status_code == 200
        wrong_list = resp.json()
        assert len(wrong_list) >= 1
        assert wrong_list[0]["wrong_count"] >= 1


class TestWeakPoints:
    def test_weak_points_empty(self, client, child_setup):
        """没有答题记录时，薄弱点为空"""
        child_id, headers = child_setup
        resp = client.get(f"/api/reports/{child_id}/weak_points", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "weak_points" in data
        assert data["weak_points"] == []

    def test_weak_points_after_errors(self, client, child_setup, questions_in_db):
        """答错若干题后，出现薄弱点"""
        child_id, headers = child_setup
        mission = client.post(f"/api/missions/{child_id}/today", headers=headers).json()

        # 答错前 3 道题
        for q in mission["questions"][:3]:
            client.post("/api/missions/answer", json={
                "mission_question_id": q["mission_question_id"],
                "submitted_answer": "99999",
                "attempt": 3,
            }, headers=headers)

        resp = client.get(f"/api/reports/{child_id}/weak_points", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["period_days"] == 7
        # 有答错记录，薄弱点 >= 1
        assert len(data["weak_points"]) >= 1


class TestWeeklyReport:
    def test_weekly_report_no_data(self, client, child_setup):
        """没有数据时，周报字段存在，完成天数为 0"""
        child_id, headers = child_setup
        resp = client.get(f"/api/reports/{child_id}/weekly", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "week_start" in data
        assert "week_end" in data
        assert data["completion_days"] == 0
        assert data["total_questions"] == 0
        assert "weak_points" in data
        assert "ai_summary" in data

    def test_weekly_report_has_summary_text(self, client, child_setup):
        """周报 ai_summary 是非空字符串"""
        child_id, headers = child_setup
        resp = client.get(f"/api/reports/{child_id}/weekly", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json()["ai_summary"], str)
        assert len(resp.json()["ai_summary"]) > 0
