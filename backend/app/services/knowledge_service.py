"""
知识点识别服务
规则：根据题目文本特征识别题型和知识点标签
"""
from dataclasses import dataclass
import re
from app.models.question import QuestionType, KnowledgeTag


@dataclass
class QuestionAnalysis:
    """题目分析结果"""
    question_type: QuestionType
    knowledge_tag: KnowledgeTag
    difficulty: int           # 1=简单, 2=中等, 3=困难
    normalized_text: str


def _contains_multiply(text: str) -> bool:
    return '×' in text or '*' in text or '✕' in text


def _contains_divide(text: str) -> bool:
    return '÷' in text or '/' in text


def _contains_add(text: str) -> bool:
    return '+' in text or '＋' in text


def _contains_sub(text: str) -> bool:
    # 避免把负数符号当减号（简化处理：有'-'就认为有减法）
    return '-' in text or '－' in text


def _is_unit_conversion(text: str) -> bool:
    """是否是单位换算题"""
    unit_keywords = ['千米', '公里', '米', '分米', '厘米', '毫米',
                     '千克', '公斤', '克', '吨', '小时', '分钟', '秒']
    has_unit = any(kw in text for kw in unit_keywords)
    has_blank = '_' in text or '＿' in text or '？' in text or '?' in text
    return has_unit and has_blank


def _is_word_problem(text: str) -> bool:
    """是否是应用题（含中文句子描述）"""
    # 如果文本较长且含有中文汉字（非单位词），可能是应用题
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    # 去除常见单位词
    unit_words = {'千', '米', '公', '里', '分', '厘', '毫', '克', '吨', '小', '时', '秒'}
    non_unit_chinese = [c for c in chinese_chars if c not in unit_words]
    return len(non_unit_chinese) >= 4  # 超过4个非单位汉字，认为是应用题


def _is_mixed_operation(text: str) -> bool:
    """是否是混合运算（含多种运算符）"""
    op_count = 0
    if _contains_add(text):
        op_count += 1
    if _contains_sub(text):
        op_count += 1
    if _contains_multiply(text):
        op_count += 1
    if _contains_divide(text):
        op_count += 1
    return op_count >= 2


def _check_add_carry(text: str) -> bool:
    """
    判断加法是否有进位（个位相加>=10）
    从表达式中提取两个数字，检查个位之和
    """
    # 提取所有数字
    nums = re.findall(r'\d+', text)
    if len(nums) < 2:
        return False
    a, b = int(nums[0]), int(nums[1])
    # 检查个位进位
    ones_sum = (a % 10) + (b % 10)
    if ones_sum >= 10:
        return True
    # 检查十位进位
    tens_sum = (a // 10 % 10) + (b // 10 % 10)
    if tens_sum >= 10:
        return True
    return False


def _check_sub_borrow(text: str) -> bool:
    """
    判断减法是否有借位（个位被减数 < 减数个位）
    """
    nums = re.findall(r'\d+', text)
    if len(nums) < 2:
        return False
    a, b = int(nums[0]), int(nums[1])
    if (a % 10) < (b % 10):
        return True
    return False


def _estimate_difficulty(text: str, knowledge_tag: KnowledgeTag) -> int:
    """估算难度"""
    nums = re.findall(r'\d+', text)
    max_num = max((int(n) for n in nums), default=0)

    if knowledge_tag in (KnowledgeTag.MIXED_OPERATION, KnowledgeTag.WORD_PROBLEM):
        return 3 if max_num > 50 else 2

    if knowledge_tag in (KnowledgeTag.ADD_WITH_CARRY, KnowledgeTag.SUB_WITH_BORROW,
                         KnowledgeTag.MULTIPLY_TABLE):
        return 2

    if max_num <= 10:
        return 1

    return 1


class KnowledgePointService:
    """知识点识别服务"""

    @staticmethod
    def identify(question_text: str) -> QuestionAnalysis:
        """
        识别题目的题型和知识点

        Args:
            question_text: 题目文本

        Returns:
            QuestionAnalysis
        """
        text = question_text.strip()
        normalized = text

        # 1. 单位换算
        if _is_unit_conversion(text):
            return QuestionAnalysis(
                question_type=QuestionType.UNIT_CONVERT,
                knowledge_tag=KnowledgeTag.UNIT_CONVERSION,
                difficulty=2,
                normalized_text=normalized,
            )

        # 2. 应用题
        if _is_word_problem(text):
            return QuestionAnalysis(
                question_type=QuestionType.WORD_PROBLEM,
                knowledge_tag=KnowledgeTag.WORD_PROBLEM,
                difficulty=3,
                normalized_text=normalized,
            )

        # 3. 混合运算（含两种以上运算符）
        if _is_mixed_operation(text):
            tag = KnowledgeTag.MIXED_OPERATION
            return QuestionAnalysis(
                question_type=QuestionType.MIXED_CALC,
                knowledge_tag=tag,
                difficulty=_estimate_difficulty(text, tag),
                normalized_text=normalized,
            )

        # 4. 乘法
        if _contains_multiply(text):
            tag = KnowledgeTag.MULTIPLY_TABLE
            return QuestionAnalysis(
                question_type=QuestionType.ORAL_CALC,
                knowledge_tag=tag,
                difficulty=_estimate_difficulty(text, tag),
                normalized_text=normalized,
            )

        # 5. 除法
        if _contains_divide(text):
            tag = KnowledgeTag.MULTIPLY_TABLE  # 除法也归在乘除法知识点
            return QuestionAnalysis(
                question_type=QuestionType.ORAL_CALC,
                knowledge_tag=tag,
                difficulty=_estimate_difficulty(text, tag),
                normalized_text=normalized,
            )

        # 6. 加法
        if _contains_add(text):
            if _check_add_carry(text):
                tag = KnowledgeTag.ADD_WITH_CARRY
            else:
                tag = KnowledgeTag.ADD_NO_CARRY
            return QuestionAnalysis(
                question_type=QuestionType.ORAL_CALC,
                knowledge_tag=tag,
                difficulty=_estimate_difficulty(text, tag),
                normalized_text=normalized,
            )

        # 7. 减法
        if _contains_sub(text):
            if _check_sub_borrow(text):
                tag = KnowledgeTag.SUB_WITH_BORROW
            else:
                tag = KnowledgeTag.SUB_NO_BORROW
            return QuestionAnalysis(
                question_type=QuestionType.ORAL_CALC,
                knowledge_tag=tag,
                difficulty=_estimate_difficulty(text, tag),
                normalized_text=normalized,
            )

        # 默认：无法识别
        return QuestionAnalysis(
            question_type=QuestionType.FILL_BLANK,
            knowledge_tag=KnowledgeTag.ADD_NO_CARRY,
            difficulty=1,
            normalized_text=normalized,
        )
