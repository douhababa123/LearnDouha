"""
TDD - 反馈服务测试
规则：答对给鼓励，答错第一次不揭示答案，多次后提供提示
"""
import pytest
from app.services.feedback_service import FeedbackService
from app.models.learning import MasteryLevel


class TestFeedbackServiceCorrect:
    """测试答对时的反馈"""

    def test_correct_answer_is_positive(self):
        """答对时反馈是积极的"""
        feedback = FeedbackService.generate_feedback(is_correct=True, attempt=1)
        assert feedback.is_positive is True

    def test_correct_answer_has_text(self):
        """答对时有鼓励文案"""
        feedback = FeedbackService.generate_feedback(is_correct=True, attempt=1)
        assert len(feedback.message) > 0

    def test_correct_answer_advances_story(self):
        """答对时可以推进剧情"""
        feedback = FeedbackService.generate_feedback(is_correct=True, attempt=1)
        assert feedback.show_story_advance is True

    def test_correct_messages_are_varied(self):
        """答对时文案有多样性（至少有2种以上不同文案）"""
        messages = set()
        for _ in range(10):
            feedback = FeedbackService.generate_feedback(is_correct=True, attempt=1)
            messages.add(feedback.message)
        assert len(messages) >= 2


class TestFeedbackServiceWrongFirstAttempt:
    """测试第一次答错时的反馈"""

    def test_first_wrong_is_encouraging(self):
        """第一次答错，反馈应鼓励，不打击"""
        feedback = FeedbackService.generate_feedback(is_correct=False, attempt=1)
        assert feedback.is_positive is False  # 不是答对的正向反馈
        assert feedback.show_answer is False  # 第一次不揭示答案

    def test_first_wrong_no_answer_revealed(self):
        """第一次答错，不直接给答案"""
        feedback = FeedbackService.generate_feedback(is_correct=False, attempt=1)
        assert feedback.show_answer is False

    def test_first_wrong_encourages_retry(self):
        """第一次答错，引导再试一次"""
        feedback = FeedbackService.generate_feedback(is_correct=False, attempt=1)
        assert feedback.can_retry is True

    def test_first_wrong_hint_text(self):
        """第一次答错，有轻量提示"""
        feedback = FeedbackService.generate_feedback(is_correct=False, attempt=1)
        assert len(feedback.message) > 0


class TestFeedbackServiceWrongSecondAttempt:
    """测试第二次答错时的反馈"""

    def test_second_wrong_still_encouraging(self):
        """第二次答错，仍然鼓励"""
        feedback = FeedbackService.generate_feedback(is_correct=False, attempt=2)
        assert feedback.can_retry is True

    def test_second_wrong_may_show_hint(self):
        """第二次答错，可以显示提示"""
        feedback = FeedbackService.generate_feedback(is_correct=False, attempt=2)
        assert feedback.hint is not None or len(feedback.message) > 0


class TestFeedbackServiceWrongThirdAttempt:
    """测试第三次及以上答错"""

    def test_third_wrong_shows_explanation(self):
        """第三次答错，触发讲解"""
        feedback = FeedbackService.generate_feedback(is_correct=False, attempt=3)
        assert feedback.show_explanation is True

    def test_third_wrong_shows_answer(self):
        """第三次答错，揭示答案"""
        feedback = FeedbackService.generate_feedback(is_correct=False, attempt=3)
        assert feedback.show_answer is True


class TestFeedbackServiceMessages:
    """测试鼓励文案内容符合需求"""

    EXPECTED_ENCOURAGING_PHRASES = ["再想一想", "已经很接近", "别着急", "可以再试", "一步一步"]

    def test_wrong_message_is_not_negative(self):
        """答错反馈文案不应含负面词汇"""
        NEGATIVE_WORDS = ["错了", "不对", "失败", "差劲"]
        feedback = FeedbackService.generate_feedback(is_correct=False, attempt=1)
        for word in NEGATIVE_WORDS:
            assert word not in feedback.message

    def test_correct_message_is_positive(self):
        """答对反馈文案包含鼓励词"""
        POSITIVE_WORDS = ["棒", "厉害", "很好", "太棒", "对了", "正确", "继续", "加油"]
        feedback = FeedbackService.generate_feedback(is_correct=True, attempt=1)
        assert any(word in feedback.message for word in POSITIVE_WORDS)
