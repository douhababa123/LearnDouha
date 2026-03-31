"""
掌握度判断服务
规则：
  - 无答题记录 -> NOT_STARTED
  - 原题错 + 类似题多数错 -> LEARNING（学习中，未掌握）
  - 原题错 + 类似题多数对 -> INITIAL（初步掌握）
  - 高正确率（>80%） -> MASTERED（已掌握）
"""
from typing import Dict, Any, List
from app.models.learning import MasteryLevel


# 掌握度阈值
MASTERY_THRESHOLD = 0.80   # 正确率>=80%才认为掌握
INITIAL_THRESHOLD = 0.60   # 正确率>=60%认为初步掌握
WEAK_POINT_THRESHOLD = 0.30  # 错误率>=30%认为是薄弱点


class MasteryService:
    """掌握度判断服务"""

    @staticmethod
    def evaluate(records: Dict[str, int]) -> MasteryLevel:
        """
        评估知识点掌握程度

        Args:
            records: {
                "original_attempts": 原题答题次数,
                "original_correct": 原题答对次数,
                "similar_attempts": 类似题答题次数,
                "similar_correct": 类似题答对次数,
            }

        Returns:
            MasteryLevel
        """
        orig_attempts = records.get("original_attempts", 0)
        orig_correct = records.get("original_correct", 0)
        sim_attempts = records.get("similar_attempts", 0)
        sim_correct = records.get("similar_correct", 0)

        total_attempts = orig_attempts + sim_attempts
        total_correct = orig_correct + sim_correct

        # 无任何答题记录
        if total_attempts == 0:
            return MasteryLevel.NOT_STARTED

        # 整体正确率
        overall_rate = total_correct / total_attempts

        # 已掌握
        if overall_rate >= MASTERY_THRESHOLD:
            return MasteryLevel.MASTERED

        # 初步掌握：原题可能有错，但类似题表现较好（>=60%）-> 初步掌握
        if sim_attempts > 0:
            sim_rate = sim_correct / sim_attempts
            if sim_rate >= INITIAL_THRESHOLD:
                return MasteryLevel.INITIAL
        elif orig_attempts > 0:
            # 无类似题时，仅凭原题判断
            orig_rate = orig_correct / orig_attempts
            if orig_rate >= MASTERY_THRESHOLD:
                return MasteryLevel.MASTERED
            if orig_rate >= INITIAL_THRESHOLD:
                return MasteryLevel.INITIAL

        return MasteryLevel.LEARNING

    @staticmethod
    def get_weak_points(
        mastery_data: Dict[str, Dict[str, int]],
        top_n: int = 3,
        threshold: float = WEAK_POINT_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        """
        获取薄弱知识点列表

        Args:
            mastery_data: {
                "knowledge_tag": {"total": 总题数, "correct": 答对数}
            }
            top_n: 返回最多几个薄弱点
            threshold: 错误率阈值（大于此值才认为是薄弱点）

        Returns:
            List of {"knowledge_tag": ..., "error_rate": ..., "total": ...}
            按错误率降序排列
        """
        if not mastery_data:
            return []

        weak_points = []
        for tag, stats in mastery_data.items():
            total = stats.get("total", 0)
            if total == 0:
                continue
            correct = stats.get("correct", 0)
            error_rate = 1 - correct / total
            if error_rate > threshold:
                weak_points.append({
                    "knowledge_tag": tag,
                    "error_rate": round(error_rate, 4),
                    "total": total,
                    "correct": correct,
                })

        # 按错误率降序
        weak_points.sort(key=lambda x: x["error_rate"], reverse=True)

        return weak_points[:top_n]
