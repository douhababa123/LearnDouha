"""
报告路由 - 家长端学习总览、错题、薄弱点、周报告
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.user import User, Child
from app.models.learning import (
    DailyMission, AnswerRecord, WrongQuestionRecord,
    MasteryRecord, StreakRecord, WeeklyReport, MasteryLevel
)
from app.models.question import ParsedQuestion
from app.routers.auth import get_current_user
from app.services.mastery_service import MasteryService

router = APIRouter()


@router.get("/{child_id}/overview", summary="今日学习总览（家长端）")
def get_today_overview(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    mission = db.query(DailyMission).filter(
        DailyMission.child_id == child_id,
        DailyMission.mission_date == today
    ).first()

    streak = db.query(StreakRecord).filter(StreakRecord.child_id == child_id).first()

    return {
        "date": str(today),
        "is_completed": mission.is_completed if mission else False,
        "completed_questions": mission.completed_questions if mission else 0,
        "total_questions": mission.total_questions if mission else 0,
        "accuracy_rate": mission.accuracy_rate if mission else 0.0,
        "current_streak": streak.current_streak if streak else 0,
        "total_checkins": streak.total_checkins if streak else 0,
    }


@router.get("/{child_id}/wrong_questions", summary="错题列表")
def get_wrong_questions(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wrong_records = db.query(WrongQuestionRecord).filter(
        WrongQuestionRecord.child_id == child_id
    ).order_by(WrongQuestionRecord.last_wrong_at.desc()).limit(50).all()

    result = []
    for rec in wrong_records:
        q = db.query(ParsedQuestion).filter(ParsedQuestion.id == rec.question_id).first()
        if q:
            result.append({
                "question_id": q.id,
                "text": q.normalized_text,
                "knowledge_tag": q.knowledge_tag,
                "wrong_count": rec.wrong_count,
                "is_reinforced": rec.is_reinforced,
                "is_mastered": rec.is_mastered,
                "last_wrong_at": str(rec.last_wrong_at),
            })
    return result


@router.get("/{child_id}/weak_points", summary="薄弱知识点分析")
def get_weak_points(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分析最近7天的知识点表现，找出薄弱点"""
    seven_days_ago = date.today() - timedelta(days=7)

    # 获取最近7天的答题记录
    records = db.query(AnswerRecord).filter(
        AnswerRecord.child_id == child_id,
        AnswerRecord.answered_at >= seven_days_ago,
    ).all()

    # 按知识点聚合
    mastery_data = {}
    for rec in records:
        q = db.query(ParsedQuestion).filter(ParsedQuestion.id == rec.question_id).first()
        if not q:
            continue
        tag = q.knowledge_tag
        if tag not in mastery_data:
            mastery_data[tag] = {"total": 0, "correct": 0}
        mastery_data[tag]["total"] += 1
        if rec.is_correct:
            mastery_data[tag]["correct"] += 1

    weak_points = MasteryService.get_weak_points(mastery_data, top_n=5)
    return {
        "period_days": 7,
        "weak_points": weak_points,
    }


@router.get("/{child_id}/weekly", summary="本周学习报告")
def get_weekly_report(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成本周学习报告"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # 本周一
    week_end = week_start + timedelta(days=6)

    # 本周每日任务统计
    missions = db.query(DailyMission).filter(
        DailyMission.child_id == child_id,
        DailyMission.mission_date >= week_start,
        DailyMission.mission_date <= week_end,
    ).all()

    completion_days = sum(1 for m in missions if m.is_completed)
    total_questions = sum(m.completed_questions for m in missions)
    total_correct = sum(m.correct_count for m in missions)
    avg_accuracy = round(total_correct / total_questions, 4) if total_questions > 0 else 0.0

    # 薄弱点分析
    records = db.query(AnswerRecord).filter(
        AnswerRecord.child_id == child_id,
        AnswerRecord.answered_at >= week_start,
    ).all()

    mastery_data = {}
    for rec in records:
        q = db.query(ParsedQuestion).filter(ParsedQuestion.id == rec.question_id).first()
        if not q:
            continue
        tag = q.knowledge_tag
        if tag not in mastery_data:
            mastery_data[tag] = {"total": 0, "correct": 0}
        mastery_data[tag]["total"] += 1
        if rec.is_correct:
            mastery_data[tag]["correct"] += 1

    weak_points = MasteryService.get_weak_points(mastery_data, top_n=3)
    # 进步最大的知识点（错误率较低的）
    progress_points = sorted(
        [
            {"knowledge_tag": tag, "accuracy": round(s["correct"] / s["total"], 4)}
            for tag, s in mastery_data.items()
            if s["total"] > 0
        ],
        key=lambda x: x["accuracy"],
        reverse=True,
    )[:3]

    # 简单AI总结（规则生成）
    summary = _generate_summary(
        completion_days=completion_days,
        avg_accuracy=avg_accuracy,
        weak_points=weak_points,
    )

    return {
        "week_start": str(week_start),
        "week_end": str(week_end),
        "completion_days": completion_days,
        "total_questions": total_questions,
        "avg_accuracy": avg_accuracy,
        "weak_points": weak_points,
        "progress_points": progress_points,
        "ai_summary": summary,
    }


def _generate_summary(completion_days: int, avg_accuracy: float, weak_points: list) -> str:
    """规则生成周报总结文案"""
    parts = []
    if completion_days >= 5:
        parts.append(f"本周完成了{completion_days}天练习，坚持得非常好！")
    elif completion_days >= 3:
        parts.append(f"本周完成了{completion_days}天练习，再加把劲！")
    else:
        parts.append(f"本周完成了{completion_days}天练习，下周争取每天都完成哦。")

    if avg_accuracy >= 0.9:
        parts.append(f"正确率达到{int(avg_accuracy * 100)}%，真的很厉害！")
    elif avg_accuracy >= 0.7:
        parts.append(f"正确率{int(avg_accuracy * 100)}%，表现不错，继续加油！")
    else:
        parts.append(f"正确率{int(avg_accuracy * 100)}%，需要多加练习。")

    if weak_points:
        tags_str = "、".join(wp["knowledge_tag"] for wp in weak_points[:2])
        parts.append(f"建议重点练习：{tags_str}。")

    return "".join(parts)
