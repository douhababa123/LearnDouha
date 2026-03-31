"""
TDD - 知识点识别服务测试
规则：根据题目文本识别题型和知识点
"""
import pytest
from app.services.knowledge_service import KnowledgePointService
from app.models.question import QuestionType, KnowledgeTag


class TestKnowledgePointServiceAddition:
    """测试：加法题目识别"""

    def test_identify_add_with_carry(self):
        """识别进位加法知识点"""
        result = KnowledgePointService.identify("35 + 27")
        assert result.knowledge_tag == KnowledgeTag.ADD_WITH_CARRY

    def test_identify_add_no_carry(self):
        """识别不进位加法知识点"""
        result = KnowledgePointService.identify("23 + 14")
        assert result.knowledge_tag == KnowledgeTag.ADD_NO_CARRY

    def test_identify_addition_question_type(self):
        """识别加法题型为口算题"""
        result = KnowledgePointService.identify("35 + 27")
        assert result.question_type == QuestionType.ORAL_CALC

    def test_add_boundary_100(self):
        """边界：进位到100"""
        result = KnowledgePointService.identify("56 + 44")
        assert result.knowledge_tag == KnowledgeTag.ADD_WITH_CARRY


class TestKnowledgePointServiceSubtraction:
    """测试：减法题目识别"""

    def test_identify_sub_with_borrow(self):
        """识别退位减法"""
        result = KnowledgePointService.identify("72 - 38")
        assert result.knowledge_tag == KnowledgeTag.SUB_WITH_BORROW

    def test_identify_sub_no_borrow(self):
        """识别不退位减法"""
        result = KnowledgePointService.identify("45 - 23")
        assert result.knowledge_tag == KnowledgeTag.SUB_NO_BORROW

    def test_subtraction_question_type(self):
        """减法是口算题型"""
        result = KnowledgePointService.identify("45 - 23")
        assert result.question_type == QuestionType.ORAL_CALC


class TestKnowledgePointServiceMultiplication:
    """测试：乘法题目识别"""

    def test_identify_multiply_table_star(self):
        """乘号 * 识别为表内乘法"""
        result = KnowledgePointService.identify("6 * 8")
        assert result.knowledge_tag == KnowledgeTag.MULTIPLY_TABLE

    def test_identify_multiply_table_chinese(self):
        """乘号 × 识别为表内乘法"""
        result = KnowledgePointService.identify("7 × 9")
        assert result.knowledge_tag == KnowledgeTag.MULTIPLY_TABLE

    def test_multiplication_question_type(self):
        """乘法是口算题型"""
        result = KnowledgePointService.identify("7 × 9")
        assert result.question_type == QuestionType.ORAL_CALC


class TestKnowledgePointServiceUnitConversion:
    """测试：单位换算识别"""

    def test_identify_unit_km_m(self):
        """识别千米=米的单位换算"""
        result = KnowledgePointService.identify("1千米 = ___米")
        assert result.knowledge_tag == KnowledgeTag.UNIT_CONVERSION
        assert result.question_type == QuestionType.UNIT_CONVERT

    def test_identify_unit_m_cm(self):
        """识别米=厘米的单位换算"""
        result = KnowledgePointService.identify("3米 = ___厘米")
        assert result.knowledge_tag == KnowledgeTag.UNIT_CONVERSION

    def test_identify_unit_cm_mm(self):
        """识别厘米=毫米的单位换算"""
        result = KnowledgePointService.identify("5厘米 = ___毫米")
        assert result.knowledge_tag == KnowledgeTag.UNIT_CONVERSION


class TestKnowledgePointServiceMixedOperation:
    """测试：混合运算识别"""

    def test_identify_mixed_add_sub(self):
        """识别加减混合为混合运算"""
        result = KnowledgePointService.identify("10 + 20 - 5")
        assert result.knowledge_tag == KnowledgeTag.MIXED_OPERATION

    def test_identify_mixed_with_multiply(self):
        """识别含乘法的混合运算"""
        result = KnowledgePointService.identify("3 × 4 + 5")
        assert result.knowledge_tag == KnowledgeTag.MIXED_OPERATION
        assert result.question_type == QuestionType.MIXED_CALC


class TestKnowledgePointServiceDifficulty:
    """测试：难度估算"""

    def test_easy_small_numbers(self):
        """小数字加法难度为1"""
        result = KnowledgePointService.identify("3 + 4")
        assert result.difficulty == 1

    def test_medium_carry_addition(self):
        """进位加法难度为2"""
        result = KnowledgePointService.identify("35 + 47")
        assert result.difficulty == 2

    def test_hard_mixed_operation(self):
        """混合运算难度为2或3"""
        result = KnowledgePointService.identify("3 × 4 + 5")
        assert result.difficulty >= 2
