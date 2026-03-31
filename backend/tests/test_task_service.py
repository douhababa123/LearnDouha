"""
TDD - 每日任务生成服务测试
规则：按比例（基础60%/复习15%/错题回流15%/应用题10%）生成任务
"""
import pytest
from app.services.task_service import TaskGenerationService
from app.models.question import KnowledgeTag, QuestionType


def make_question(qid: int, knowledge_tag: KnowledgeTag,
                  question_type: QuestionType = QuestionType.ORAL_CALC,
                  difficulty: int = 1):
    """辅助函数：创建模拟题目对象"""
    return {
        "id": qid,
        "knowledge_tag": knowledge_tag,
        "question_type": question_type,
        "difficulty": difficulty,
        "normalized_text": f"题目{qid}",
        "correct_answer": "10",
        "is_usable": True,
    }


def make_wrong_record(question_id: int, wrong_count: int = 2):
    """辅助函数：创建错题记录"""
    return {
        "question_id": question_id,
        "wrong_count": wrong_count,
        "is_mastered": False,
    }


class TestTaskGenerationServiceBasic:
    """测试基础任务生成"""

    def setup_method(self):
        """准备题目池"""
        self.question_pool = [
            make_question(i, KnowledgeTag.ADD_WITH_CARRY) for i in range(1, 31)
        ]
        self.service = TaskGenerationService()

    def test_generates_20_questions_by_default(self):
        """默认生成20道题"""
        task = self.service.generate(
            question_pool=self.question_pool,
            wrong_records=[],
            target_count=20
        )
        assert len(task.questions) == 20

    def test_generates_specified_count(self):
        """按指定数量生成"""
        task = self.service.generate(
            question_pool=self.question_pool,
            wrong_records=[],
            target_count=10
        )
        assert len(task.questions) == 10

    def test_no_duplicate_questions(self):
        """同一道题不重复出现"""
        task = self.service.generate(
            question_pool=self.question_pool,
            wrong_records=[],
            target_count=20
        )
        ids = [q["id"] for q in task.questions]
        assert len(ids) == len(set(ids))


class TestTaskGenerationServiceRatio:
    """测试任务题目比例"""

    def setup_method(self):
        """准备足够多的不同类型题目"""
        self.basic_questions = [
            make_question(i, KnowledgeTag.ADD_WITH_CARRY) for i in range(1, 41)
        ]
        self.review_questions = [
            make_question(i, KnowledgeTag.SUB_WITH_BORROW) for i in range(41, 81)
        ]
        self.word_questions = [
            make_question(i, KnowledgeTag.WORD_PROBLEM, QuestionType.WORD_PROBLEM, 2)
            for i in range(81, 101)
        ]
        self.question_pool = self.basic_questions + self.review_questions + self.word_questions

        self.wrong_records = [make_wrong_record(i) for i in range(1, 5)]
        self.service = TaskGenerationService()

    def test_basic_ratio_approximately_60_percent(self):
        """基础题比例约60%"""
        task = self.service.generate(
            question_pool=self.question_pool,
            wrong_records=self.wrong_records,
            target_count=20
        )
        basic_count = sum(1 for q in task.questions if q.get("category") == "basic")
        assert basic_count >= 10  # 至少50%为基础题

    def test_wrong_recycle_present_when_wrong_records_exist(self):
        """有错题记录时，任务中应包含错题回流"""
        task = self.service.generate(
            question_pool=self.question_pool,
            wrong_records=self.wrong_records,
            target_count=20
        )
        wrong_ids = {r["question_id"] for r in self.wrong_records}
        recycle_count = sum(1 for q in task.questions if q["id"] in wrong_ids)
        assert recycle_count >= 1

    def test_no_wrong_recycle_without_wrong_records(self):
        """无错题记录时，任务中无错题回流"""
        task = self.service.generate(
            question_pool=self.question_pool,
            wrong_records=[],
            target_count=20
        )
        wrong_category = sum(1 for q in task.questions if q.get("category") == "wrong_recycle")
        assert wrong_category == 0


class TestTaskGenerationServicePoolTooSmall:
    """测试题目池不足的情况"""

    def test_generates_all_when_pool_smaller_than_target(self):
        """题库比目标数量少时，生成全部可用题目"""
        small_pool = [make_question(i, KnowledgeTag.ADD_WITH_CARRY) for i in range(1, 6)]
        service = TaskGenerationService()
        task = service.generate(
            question_pool=small_pool,
            wrong_records=[],
            target_count=20
        )
        assert len(task.questions) == len(small_pool)

    def test_returns_empty_task_for_empty_pool(self):
        """空题库返回空任务"""
        service = TaskGenerationService()
        task = service.generate(
            question_pool=[],
            wrong_records=[],
            target_count=20
        )
        assert len(task.questions) == 0


class TestTaskGenerationServiceOrdering:
    """测试题目顺序与分组"""

    def test_questions_have_category_field(self):
        """每道题目有分类标签"""
        pool = [make_question(i, KnowledgeTag.ADD_WITH_CARRY) for i in range(1, 30)]
        service = TaskGenerationService()
        task = service.generate(
            question_pool=pool,
            wrong_records=[],
            target_count=10
        )
        for q in task.questions:
            assert "category" in q
            assert q["category"] in ("basic", "review", "wrong_recycle", "story")
