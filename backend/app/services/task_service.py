"""
每日任务生成服务
规则：按比例生成任务题目
  - 基础题 60%
  - 复习题 15%
  - 错题回流 15%
  - 应用题/剧情关键题 10%
"""
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any
from app.models.question import QuestionType


@dataclass
class GeneratedTask:
    """生成的任务结果"""
    questions: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0

    def __post_init__(self):
        self.total_count = len(self.questions)


class TaskGenerationService:
    """每日任务生成服务"""

    # 题目分类比例
    RATIO_BASIC = 0.60          # 基础题 60%
    RATIO_REVIEW = 0.15         # 复习题 15%
    RATIO_WRONG_RECYCLE = 0.15  # 错题回流 15%
    RATIO_STORY = 0.10          # 应用题/剧情关键题 10%

    def generate(
        self,
        question_pool: List[Dict[str, Any]],
        wrong_records: List[Dict[str, Any]],
        target_count: int = 20,
    ) -> GeneratedTask:
        """
        生成每日任务题目列表

        Args:
            question_pool: 可用题目列表
            wrong_records: 孩子的错题记录列表
            target_count: 目标题目数量

        Returns:
            GeneratedTask
        """
        if not question_pool:
            return GeneratedTask(questions=[])

        # 如果题库不足，全部使用
        if len(question_pool) <= target_count:
            result = []
            for q in question_pool:
                q_copy = dict(q)
                q_copy["category"] = "basic"
                result.append(q_copy)
            return GeneratedTask(questions=result)

        # 计算各类数量
        wrong_ids = {r["question_id"] for r in wrong_records if not r.get("is_mastered")}

        # 区分应用题、普通题
        story_pool = [q for q in question_pool
                      if q.get("question_type") == QuestionType.WORD_PROBLEM]
        non_story_pool = [q for q in question_pool
                          if q.get("question_type") != QuestionType.WORD_PROBLEM]

        # 错题回流池（从普通题中取）
        wrong_pool = [q for q in non_story_pool if q["id"] in wrong_ids]
        # 基础+复习池（非错题）
        fresh_pool = [q for q in non_story_pool if q["id"] not in wrong_ids]

        # 计算各类实际数量
        n_wrong = min(
            round(target_count * self.RATIO_WRONG_RECYCLE),
            len(wrong_pool)
        ) if wrong_ids else 0

        n_story = min(round(target_count * self.RATIO_STORY), len(story_pool))
        n_remaining = target_count - n_wrong - n_story

        # 基础题 vs 复习题
        n_basic = round(n_remaining * (self.RATIO_BASIC / (self.RATIO_BASIC + self.RATIO_REVIEW)))
        n_review = n_remaining - n_basic

        # 从各池中采样（不重复）
        random.shuffle(fresh_pool)
        random.shuffle(wrong_pool)
        random.shuffle(story_pool)

        basic_questions = fresh_pool[:n_basic]
        review_questions = fresh_pool[n_basic: n_basic + n_review]
        wrong_questions = wrong_pool[:n_wrong]
        story_questions = story_pool[:n_story]

        # 标记分类
        result = []
        for q in basic_questions:
            q_copy = dict(q)
            q_copy["category"] = "basic"
            result.append(q_copy)
        for q in review_questions:
            q_copy = dict(q)
            q_copy["category"] = "review"
            result.append(q_copy)
        for q in wrong_questions:
            q_copy = dict(q)
            q_copy["category"] = "wrong_recycle"
            result.append(q_copy)
        for q in story_questions:
            q_copy = dict(q)
            q_copy["category"] = "story"
            result.append(q_copy)

        # 打乱顺序（避免孩子察觉模式）
        random.shuffle(result)

        return GeneratedTask(questions=result)
