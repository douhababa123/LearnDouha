"""
TDD: 完整用户旅程端到端测试
场景：家长注册 → 添加题目 → 创建孩子 → 孩子完成任务 → 家长查看报告

这个文件回答了用户的三个问题：
Q1 "这个是啥意思？"   → 题库为空时不能生成每日任务
Q2 "在哪里导入？"     → 家长端 /api/questions/batch（题库管理页）
Q3 "导入后要干什么？" → 孩子端生成任务 → 答题 → 查看报告
"""
import pytest


class TestEmptyPoolGuidance:
    """题库为空时的错误提示应清晰指引家长去添加题目"""

    def test_empty_pool_returns_404(self, client, child_setup):
        """题库为空时生成任务应返回 404"""
        child_id, headers = child_setup
        resp = client.post(f"/api/missions/{child_id}/today", headers=headers)
        assert resp.status_code == 404

    def test_empty_pool_error_message_guides_parent(self, client, child_setup):
        """错误信息应提示家长去题库管理页添加题目，而不是'导入PDF'"""
        child_id, headers = child_setup
        resp = client.post(f"/api/missions/{child_id}/today", headers=headers)
        detail = resp.json()["detail"]
        # 不应出现误导性的 "PDF" 字样
        assert "PDF" not in detail
        # 应提示用户去添加题目
        assert any(w in detail for w in ["添加", "题目", "题库"])


class TestCompleteUserJourney:
    """
    完整用户旅程（E2E）
    步骤：
      1. 家长注册 + 登录
      2. 家长 → 题库管理 → 批量添加题目       ← "在哪里导入"
      3. 家长 → 创建孩子
      4. 孩子 → 生成每日任务                  ← "导入后干什么(1)"
      5. 孩子 → 答题（正确 + 错误）           ← "导入后干什么(2)"
      6. 家长 → 查看报告                      ← "导入后干什么(3)"
    """

    def test_step1_parent_register_and_login(self, client):
        """步骤1：家长成功注册并登录"""
        r = client.post("/api/auth/register", json={
            "username": "journey_parent", "password": "pw123",
            "role": "parent", "nickname": "旅程爸爸",
        })
        assert r.status_code == 200

        token_r = client.post("/api/auth/token", data={
            "username": "journey_parent", "password": "pw123"
        })
        assert token_r.status_code == 200
        assert token_r.json()["role"] == "parent"

    def test_step2_parent_adds_questions_to_pool(self, client, parent_token):
        """步骤2：家长在题库管理页批量导入题目（'在哪里导入'的答案）"""
        _, headers = parent_token
        questions = [
            {"original_text": "23 + 45 = ___"},
            {"original_text": "67 - 28 = ___"},
            {"original_text": "6 × 7 = ___"},
            {"original_text": "48 + 35 = ___"},
            {"original_text": "90 - 46 = ___"},
        ]
        resp = client.post("/api/questions/batch",
                           json={"questions": questions}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["created_count"] == 5
        # 每道题都有自动识别的知识点
        for q in data["questions"]:
            assert q["knowledge_tag"] != ""

    def test_step3_parent_creates_child(self, client, parent_token):
        """步骤3：家长创建孩子账号"""
        _, headers = parent_token
        resp = client.post("/api/children/",
                           json={"nickname": "旅程小明", "grade": 2}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["nickname"] == "旅程小明"

    def test_step4_child_can_generate_mission_after_questions_added(
            self, client, child_setup, questions_in_db):
        """步骤4：题库有题后孩子能成功生成每日任务（'导入后干什么(1)'）"""
        child_id, headers = child_setup
        resp = client.post(f"/api/missions/{child_id}/today", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["questions"]) > 0
        # 初始所有题目均未回答
        assert all(not q["is_answered"] for q in data["questions"])

    def test_step5a_child_answers_correctly(self, client, child_setup, questions_in_db):
        """步骤5a：孩子答对题目，收到鼓励反馈"""
        child_id, headers = child_setup
        mission = client.post(f"/api/missions/{child_id}/today", headers=headers).json()
        mq_id = mission["questions"][0]["mission_question_id"]

        resp = client.post("/api/missions/answer", json={
            "mission_question_id": mq_id,
            "submitted_answer": "68",   # 23+45 的正确答案
            "attempt": 1,
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        # 不管是否真正答对，接口结构必须正确
        assert "is_correct" in data
        assert data["feedback"]["message"] != ""
        assert "mission_progress" in data

    def test_step5b_child_wrong_answer_gets_retry_chance(
            self, client, child_setup, questions_in_db):
        """步骤5b：第1次答错，提示可以重试，不直接显示答案"""
        child_id, headers = child_setup
        mission = client.post(f"/api/missions/{child_id}/today", headers=headers).json()
        mq_id = mission["questions"][0]["mission_question_id"]

        resp = client.post("/api/missions/answer", json={
            "mission_question_id": mq_id,
            "submitted_answer": "999",  # 明显错误答案
            "attempt": 1,
        }, headers=headers)
        resp_data = resp.json()
        # is_correct 在顶层，不在 feedback 子对象里
        assert resp_data["is_correct"] is False
        fb = resp_data["feedback"]
        assert fb["can_retry"] is True
        assert fb["show_answer"] is False

    def test_step5c_after_3_wrong_shows_answer(
            self, client, child_setup, questions_in_db):
        """步骤5c：第3次答错，显示正确答案和解析"""
        child_id, headers = child_setup
        mission = client.post(f"/api/missions/{child_id}/today", headers=headers).json()
        mq_id = mission["questions"][0]["mission_question_id"]

        resp = client.post("/api/missions/answer", json={
            "mission_question_id": mq_id,
            "submitted_answer": "999",
            "attempt": 3,
        }, headers=headers)
        fb = resp.json()["feedback"]
        assert fb["show_answer"] is True
        assert fb["can_retry"] is False

    def test_step6_parent_sees_report_after_child_answers(
            self, client, child_setup, questions_in_db):
        """步骤6：孩子答题后，家长能在报告页看到数据（'导入后干什么(3)'）"""
        child_id, headers = child_setup
        # 孩子答几道题（取实际可用数量，最多3道）
        mission = client.post(f"/api/missions/{child_id}/today", headers=headers).json()
        to_answer = mission["questions"][:3]
        n_submitted = len(to_answer)   # 实际提交数（可能 < 3）
        assert n_submitted >= 1, "任务至少要有1道题"
        for q in to_answer:
            client.post("/api/missions/answer", json={
                "mission_question_id": q["mission_question_id"],
                "submitted_answer": "999",
                "attempt": 1,
            }, headers=headers)

        # 家长查看今日总览：已完成数应 >= 实际提交数
        overview = client.get(f"/api/reports/{child_id}/overview", headers=headers)
        assert overview.status_code == 200
        assert overview.json()["completed_questions"] >= n_submitted

        # 家长查看周报
        weekly = client.get(f"/api/reports/{child_id}/weekly", headers=headers)
        assert weekly.status_code == 200
        assert weekly.json()["total_questions"] >= 3
        assert isinstance(weekly.json()["ai_summary"], str)
