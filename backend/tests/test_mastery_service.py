"""
TDD - 掌握度判断服务测试
规则：根据原题+类似题的答题记录判断知识点掌握程度
"""
import pytest
from app.services.mastery_service import MasteryService
from app.models.learning import MasteryLevel


class TestMasteryServiceNotMastered:
    """测试：未掌握的判断"""

    def test_original_wrong_similar_also_wrong(self):
        """原题错 + 类似题也错较多 -> 未掌握"""
        records = {
            "original_attempts": 2,
            "original_correct": 0,
            "similar_attempts": 3,
            "similar_correct": 1,
        }
        level = MasteryService.evaluate(records)
        assert level == MasteryLevel.LEARNING

    def test_all_wrong_not_mastered(self):
        """全部答错 -> 未掌握"""
        records = {
            "original_attempts": 3,
            "original_correct": 0,
            "similar_attempts": 3,
            "similar_correct": 0,
        }
        level = MasteryService.evaluate(records)
        assert level == MasteryLevel.LEARNING

    def test_no_attempts_is_not_started(self):
        """没有答题记录 -> 未开始"""
        records = {
            "original_attempts": 0,
            "original_correct": 0,
            "similar_attempts": 0,
            "similar_correct": 0,
        }
        level = MasteryService.evaluate(records)
        assert level == MasteryLevel.NOT_STARTED


class TestMasteryServiceInitialMastery:
    """测试：初步掌握的判断"""

    def test_original_wrong_similar_mostly_correct(self):
        """原题错 + 类似题多数正确 -> 初步掌握"""
        records = {
            "original_attempts": 2,
            "original_correct": 0,
            "similar_attempts": 3,
            "similar_correct": 2,
        }
        level = MasteryService.evaluate(records)
        assert level == MasteryLevel.INITIAL

    def test_mixed_performance_initial(self):
        """原题和类似题均有一定正确率 -> 初步掌握"""
        records = {
            "original_attempts": 3,
            "original_correct": 1,
            "similar_attempts": 3,
            "similar_correct": 2,
        }
        level = MasteryService.evaluate(records)
        assert level in (MasteryLevel.INITIAL, MasteryLevel.MASTERED)


class TestMasteryServiceMastered:
    """测试：已掌握的判断"""

    def test_all_correct_is_mastered(self):
        """全部答对 -> 已掌握"""
        records = {
            "original_attempts": 3,
            "original_correct": 3,
            "similar_attempts": 3,
            "similar_correct": 3,
        }
        level = MasteryService.evaluate(records)
        assert level == MasteryLevel.MASTERED

    def test_high_accuracy_is_mastered(self):
        """高正确率（>80%）-> 已掌握"""
        records = {
            "original_attempts": 5,
            "original_correct": 5,
            "similar_attempts": 3,
            "similar_correct": 3,
        }
        level = MasteryService.evaluate(records)
        assert level == MasteryLevel.MASTERED

    def test_correct_on_first_try_mastered(self):
        """首次即答对 -> 已掌握"""
        records = {
            "original_attempts": 1,
            "original_correct": 1,
            "similar_attempts": 0,
            "similar_correct": 0,
        }
        level = MasteryService.evaluate(records)
        assert level == MasteryLevel.MASTERED


class TestMasteryServiceWeakPoints:
    """测试：薄弱点识别"""

    def test_get_weak_points_returns_list(self):
        """获取薄弱点返回列表"""
        mastery_data = {
            "add_with_carry": {"total": 10, "correct": 3},
            "sub_with_borrow": {"total": 10, "correct": 8},
            "multiply_table": {"total": 10, "correct": 5},
        }
        weak_points = MasteryService.get_weak_points(mastery_data, top_n=2)
        assert isinstance(weak_points, list)
        assert len(weak_points) <= 2

    def test_weak_points_sorted_by_error_rate(self):
        """薄弱点按错误率降序排列"""
        mastery_data = {
            "add_with_carry": {"total": 10, "correct": 3},    # 错误率70%
            "sub_with_borrow": {"total": 10, "correct": 9},   # 错误率10%
            "multiply_table": {"total": 10, "correct": 5},    # 错误率50%
        }
        weak_points = MasteryService.get_weak_points(mastery_data, top_n=3)
        assert weak_points[0]["knowledge_tag"] == "add_with_carry"

    def test_no_weak_points_when_all_mastered(self):
        """全部掌握时薄弱点为空或少"""
        mastery_data = {
            "add_with_carry": {"total": 10, "correct": 10},
            "sub_with_borrow": {"total": 10, "correct": 9},
        }
        weak_points = MasteryService.get_weak_points(mastery_data, top_n=3, threshold=0.3)
        # 错误率低于30%的知识点不算薄弱点
        assert len(weak_points) == 0

    def test_empty_mastery_data_returns_empty(self):
        """空记录时返回空列表"""
        weak_points = MasteryService.get_weak_points({}, top_n=3)
        assert weak_points == []
