"""
TDD - 判分服务测试
规则：基础计算类题目由规则判分，不依赖AI
"""
import pytest
from app.services.scoring_service import ScoringService


class TestScoringServiceBasicAddition:
    """测试：100以内进位/不进位加法判分"""

    def test_correct_addition_no_carry(self):
        """不进位加法答对"""
        result = ScoringService.check_answer("23 + 14", "37")
        assert result.is_correct is True

    def test_wrong_addition_no_carry(self):
        """不进位加法答错"""
        result = ScoringService.check_answer("23 + 14", "36")
        assert result.is_correct is False

    def test_correct_addition_with_carry(self):
        """进位加法答对"""
        result = ScoringService.check_answer("35 + 27", "62")
        assert result.is_correct is True

    def test_wrong_addition_with_carry(self):
        """进位加法答错"""
        result = ScoringService.check_answer("35 + 27", "52")
        assert result.is_correct is False

    def test_addition_with_spaces(self):
        """含空格的加法，答案正确"""
        result = ScoringService.check_answer("  46 +  18  ", "64")
        assert result.is_correct is True

    def test_addition_answer_with_spaces(self):
        """答案含空格，仍可正确判断"""
        result = ScoringService.check_answer("46 + 18", "  64  ")
        assert result.is_correct is True


class TestScoringServiceBasicSubtraction:
    """测试：100以内退位/不退位减法判分"""

    def test_correct_subtraction_no_borrow(self):
        """不退位减法答对"""
        result = ScoringService.check_answer("45 - 23", "22")
        assert result.is_correct is True

    def test_wrong_subtraction_no_borrow(self):
        """不退位减法答错"""
        result = ScoringService.check_answer("45 - 23", "21")
        assert result.is_correct is False

    def test_correct_subtraction_with_borrow(self):
        """退位减法答对"""
        result = ScoringService.check_answer("72 - 38", "34")
        assert result.is_correct is True

    def test_wrong_subtraction_with_borrow(self):
        """退位减法答错"""
        result = ScoringService.check_answer("72 - 38", "44")
        assert result.is_correct is False

    def test_subtraction_result_zero(self):
        """减法结果为0"""
        result = ScoringService.check_answer("50 - 50", "0")
        assert result.is_correct is True


class TestScoringServiceMultiplication:
    """测试：表内乘法判分"""

    def test_correct_multiplication(self):
        """乘法答对"""
        result = ScoringService.check_answer("7 × 8", "56")
        assert result.is_correct is True

    def test_wrong_multiplication(self):
        """乘法答错"""
        result = ScoringService.check_answer("7 × 8", "54")
        assert result.is_correct is False

    def test_multiplication_star_symbol(self):
        """用*号表示乘法"""
        result = ScoringService.check_answer("6 * 9", "54")
        assert result.is_correct is True

    def test_multiplication_chinese_symbol(self):
        """用×号表示乘法"""
        result = ScoringService.check_answer("4 × 7", "28")
        assert result.is_correct is True

    def test_multiplication_by_zero(self):
        """乘以0"""
        result = ScoringService.check_answer("9 × 0", "0")
        assert result.is_correct is True

    def test_multiplication_by_one(self):
        """乘以1"""
        result = ScoringService.check_answer("8 × 1", "8")
        assert result.is_correct is True


class TestScoringServiceMixedExpression:
    """测试：脱式/混合运算判分"""

    def test_correct_mixed_add_then_sub(self):
        """加减混合，答对"""
        result = ScoringService.check_answer("10 + 20 - 5", "25")
        assert result.is_correct is True

    def test_wrong_mixed_expression(self):
        """混合运算，答错"""
        result = ScoringService.check_answer("10 + 20 - 5", "30")
        assert result.is_correct is False

    def test_correct_mixed_with_multiply(self):
        """含乘法的混合运算，答对"""
        result = ScoringService.check_answer("3 × 4 + 5", "17")
        assert result.is_correct is True


class TestScoringServiceUnitConversion:
    """测试：单位换算判分"""

    def test_km_to_m_correct(self):
        """千米转米，答对"""
        result = ScoringService.check_answer("1千米 = ___米", "1000")
        assert result.is_correct is True

    def test_km_to_m_wrong(self):
        """千米转米，答错"""
        result = ScoringService.check_answer("1千米 = ___米", "100")
        assert result.is_correct is False

    def test_m_to_cm_correct(self):
        """米转厘米，答对"""
        result = ScoringService.check_answer("1米 = ___厘米", "100")
        assert result.is_correct is True

    def test_cm_to_mm_correct(self):
        """厘米转毫米，答对"""
        result = ScoringService.check_answer("1厘米 = ___毫米", "10")
        assert result.is_correct is True


class TestScoringServiceEdgeCases:
    """测试边界情况"""

    def test_empty_answer_is_wrong(self):
        """空答案判为错"""
        result = ScoringService.check_answer("1 + 1", "")
        assert result.is_correct is False

    def test_non_numeric_answer(self):
        """非数字答案判为错"""
        result = ScoringService.check_answer("1 + 1", "两")
        assert result.is_correct is False

    def test_returns_correct_answer_on_wrong(self):
        """答错时返回正确答案"""
        result = ScoringService.check_answer("5 + 3", "7")
        assert result.is_correct is False
        assert result.correct_answer == "8"

    def test_returns_none_correct_answer_on_right(self):
        """答对时correct_answer不为空（仍可查阅）"""
        result = ScoringService.check_answer("5 + 3", "8")
        assert result.is_correct is True
        assert result.correct_answer == "8"
