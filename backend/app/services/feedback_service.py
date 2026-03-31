"""
即时反馈服务
规则：
  - 答对：鼓励文案 + 推进剧情
  - 第1次答错：不揭示答案，给轻量提示
  - 第2次答错：加强提示
  - 第3次及以上：揭示答案，触发讲解
"""
import random
from dataclasses import dataclass, field
from typing import Optional


# 答对鼓励文案
CORRECT_MESSAGES = [
    "太棒了！你做对了！继续加油！🎉",
    "厉害！答对了，小松鼠为你欢呼！",
    "非常好！正确！你真的很厉害！",
    "完全正确！你的数学学得真好！",
    "棒极了！继续这样，你一定能通关！",
    "对了！你今天状态超好！",
    "答对了！加油，继续前进！",
    "太厉害了！一下就算对了！",
]

# 第一次答错鼓励文案（不揭示答案）
FIRST_WRONG_MESSAGES = [
    "再想一想，我们一步一步来。",
    "已经很接近了，看看个位有没有遗漏？",
    "别着急，你可以再试一次。",
    "不要放弃，仔细再算一遍吧！",
    "几乎对了，再检查一下！",
    "你可以的，再试试看！",
]

# 第二次答错提示文案
SECOND_WRONG_MESSAGES = [
    "我们一起来想想看，从最小的位开始算。",
    "试着先算个位，再算十位，好吗？",
    "加油！你离正确答案很近了！",
    "不要紧，我们分步来想一想。",
]

# 第三次及以上答错文案
THIRD_WRONG_MESSAGES = [
    "我们一起来看看正确的答案，学一学吧！",
    "来看看这道题是怎么算的，下次你一定能行！",
    "没关系，我们来看看正确做法，下次会更好！",
]


@dataclass
class FeedbackResult:
    """反馈结果"""
    is_positive: bool           # 是否是积极反馈（答对）
    message: str                # 反馈文案
    show_answer: bool           # 是否揭示答案
    can_retry: bool             # 是否可以重试
    show_explanation: bool      # 是否触发讲解
    show_story_advance: bool    # 是否推进剧情
    hint: Optional[str] = None  # 附加提示


class FeedbackService:
    """即时反馈服务"""

    @staticmethod
    def generate_feedback(
        is_correct: bool,
        attempt: int,
        question_text: str = "",
    ) -> FeedbackResult:
        """
        生成即时反馈

        Args:
            is_correct: 是否答对
            attempt: 第几次尝试（从1开始）
            question_text: 题目文本（可选，用于生成针对性提示）

        Returns:
            FeedbackResult
        """
        if is_correct:
            return FeedbackResult(
                is_positive=True,
                message=random.choice(CORRECT_MESSAGES),
                show_answer=False,
                can_retry=False,
                show_explanation=False,
                show_story_advance=True,
            )

        # 答错分情况处理
        if attempt == 1:
            return FeedbackResult(
                is_positive=False,
                message=random.choice(FIRST_WRONG_MESSAGES),
                show_answer=False,
                can_retry=True,
                show_explanation=False,
                show_story_advance=False,
                hint=None,
            )

        if attempt == 2:
            hint = FeedbackService._generate_hint(question_text)
            return FeedbackResult(
                is_positive=False,
                message=random.choice(SECOND_WRONG_MESSAGES),
                show_answer=False,
                can_retry=True,
                show_explanation=False,
                show_story_advance=False,
                hint=hint,
            )

        # 第3次及以上
        return FeedbackResult(
            is_positive=False,
            message=random.choice(THIRD_WRONG_MESSAGES),
            show_answer=True,
            can_retry=False,
            show_explanation=True,
            show_story_advance=False,
        )

    @staticmethod
    def _generate_hint(question_text: str) -> Optional[str]:
        """根据题目文本生成简单提示"""
        if not question_text:
            return "试着从个位开始算起。"

        # 加法提示
        if '+' in question_text or '＋' in question_text:
            return "加法时注意：个位相加如果超过10，要向十位进1哦。"

        # 减法提示
        if '-' in question_text or '－' in question_text:
            return "减法时注意：如果个位不够减，要向十位借1变成10再减哦。"

        # 乘法提示
        if '×' in question_text or '*' in question_text:
            return "想一想乘法口诀表！"

        return "仔细看清楚题目，一步一步算。"
