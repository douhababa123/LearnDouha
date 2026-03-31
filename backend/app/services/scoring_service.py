"""
判分服务
规则：纯规则判分，不依赖AI
"""
from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class ScoreResult:
    """判分结果"""
    is_correct: bool
    correct_answer: str
    submitted_answer: str


# 单位换算规则表
UNIT_CONVERSION_RULES = {
    ("千米", "米"): lambda n: n * 1000,
    ("公里", "米"): lambda n: n * 1000,
    ("米", "厘米"): lambda n: n * 100,
    ("分米", "厘米"): lambda n: n * 10,
    ("厘米", "毫米"): lambda n: n * 10,
    ("千克", "克"): lambda n: n * 1000,
    ("公斤", "克"): lambda n: n * 1000,
    ("吨", "千克"): lambda n: n * 1000,
    ("小时", "分钟"): lambda n: n * 60,
    ("分钟", "秒"): lambda n: n * 60,
}


def _evaluate_expression(expr: str) -> Optional[float]:
    """
    安全地计算数学表达式
    支持 + - * × ÷ /
    """
    # 替换中文运算符为标准符号
    expr = expr.strip()
    expr = expr.replace("×", "*").replace("÷", "/").replace("－", "-").replace("＋", "+")
    # 只允许数字、运算符和空格
    if not re.match(r'^[\d\s\+\-\*\/\.\(\)]+$', expr):
        return None
    try:
        result = eval(expr, {"__builtins__": {}})  # noqa: S307
        return float(result)
    except Exception:
        return None


def _parse_unit_question(question: str):
    """
    解析单位换算题，返回 (数值, 源单位, 目标单位) 或 None
    例：'1千米 = ___米' -> (1, '千米', '米')
    """
    # 匹配模式: 数字 + 单位 + = + ___+ 单位
    pattern = r'(\d+(?:\.\d+)?)\s*(千米|公里|米|分米|厘米|毫米|千克|公斤|克|吨|小时|分钟|秒)\s*[=＝]\s*[_＿]+\s*(千米|公里|米|分米|厘米|毫米|千克|公斤|克|吨|小时|分钟|秒)'
    m = re.search(pattern, question)
    if m:
        num = float(m.group(1))
        from_unit = m.group(2)
        to_unit = m.group(3)
        return num, from_unit, to_unit
    return None


def _compute_unit_answer(question: str) -> Optional[str]:
    """计算单位换算题的正确答案"""
    parsed = _parse_unit_question(question)
    if not parsed:
        return None
    num, from_unit, to_unit = parsed
    for (src, dst), fn in UNIT_CONVERSION_RULES.items():
        if src == from_unit and dst == to_unit:
            result = fn(num)
            # 整数时去掉小数点
            if result == int(result):
                return str(int(result))
            return str(result)
    return None


def _compute_expression_answer(question: str) -> Optional[str]:
    """从表达式中计算正确答案"""
    # 提取数学表达式（去掉填空符号等）
    clean = re.sub(r'[_＿=＝？\?]', '', question)
    # 去除中文字符
    clean = re.sub(r'[\u4e00-\u9fff]', '', clean)
    val = _evaluate_expression(clean.strip())
    if val is None:
        return None
    if val == int(val):
        return str(int(val))
    return str(round(val, 4))


class ScoringService:
    """
    判分服务
    - 基础计算类：规则判分（加减乘除、混合运算）
    - 单位换算：规则判分
    - 应用题：简单字符串匹配或规则判分
    """

    @staticmethod
    def check_answer(question: str, submitted: str) -> ScoreResult:
        """
        判断答案是否正确

        Args:
            question: 题目文本，例如 "35 + 27" 或 "1千米 = ___米"
            submitted: 孩子提交的答案

        Returns:
            ScoreResult
        """
        submitted = submitted.strip()

        # 答案为空直接判错
        if not submitted:
            correct = ScoringService._compute_correct_answer(question)
            return ScoreResult(is_correct=False, correct_answer=correct or "", submitted_answer=submitted)

        # 计算正确答案
        correct = ScoringService._compute_correct_answer(question)
        if correct is None:
            # 无法自动判分，回退到字符串比较
            is_correct = submitted.strip() == question.strip()
            return ScoreResult(is_correct=is_correct, correct_answer="", submitted_answer=submitted)

        # 判断是否正确：允许数值相等（处理"08"vs"8"等格式差异）
        is_correct = ScoringService._answers_equal(correct, submitted)
        return ScoreResult(is_correct=is_correct, correct_answer=correct, submitted_answer=submitted)

    @staticmethod
    def _compute_correct_answer(question: str) -> Optional[str]:
        """计算题目的正确答案"""
        q = question.strip()

        # 先尝试单位换算
        unit_answer = _compute_unit_answer(q)
        if unit_answer is not None:
            return unit_answer

        # 再尝试数学表达式
        expr_answer = _compute_expression_answer(q)
        return expr_answer

    @staticmethod
    def _answers_equal(correct: str, submitted: str) -> bool:
        """
        比较答案是否相等
        - 支持数值比较（"8" == "08"）
        - 支持去除首尾空格
        """
        correct = correct.strip()
        submitted = submitted.strip()

        if correct == submitted:
            return True

        # 尝试数值比较
        try:
            return float(correct) == float(submitted)
        except (ValueError, TypeError):
            return False
