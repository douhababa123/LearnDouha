"""
任务路由 - 生成每日任务、提交答案、获取反馈
"""
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import User, Child
from app.models.learning import DailyMission, MissionQuestion, AnswerRecord, WrongQuestionRecord, StreakRecord
from app.models.question import ParsedQuestion
from app.routers.auth import get_current_user
from app.services.scoring_service import ScoringService
from app.services.feedback_service import FeedbackService
from app.services.task_service import TaskGenerationService
from app.services.mastery_service import MasteryService

router = APIRouter()


class SubmitAnswerRequest(BaseModel):
    mission_question_id: int
    submitted_answer: str
    attempt: int = 1


@router.post("/{child_id}/today", summary="生成今日任务")
def generate_today_mission(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()

    # 检查今天是否已有任务
    existing = db.query(DailyMission).filter(
        DailyMission.child_id == child_id,
        DailyMission.mission_date == today
    ).first()
    if existing:
        return _format_mission(existing, db)

    # 获取题目池（所有可用题目）
    questions = db.query(ParsedQuestion).filter(ParsedQuestion.is_usable == True).all()
    q_pool = [
        {
            "id": q.id,
            "knowledge_tag": q.knowledge_tag,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "normalized_text": q.normalized_text,
            "correct_answer": q.correct_answer,
            "is_usable": q.is_usable,
        }
        for q in questions
    ]

    # 获取错题记录
    wrong_records_db = db.query(WrongQuestionRecord).filter(
        WrongQuestionRecord.child_id == child_id,
        WrongQuestionRecord.is_mastered == False
    ).all()
    wrong_records = [
        {"question_id": r.question_id, "wrong_count": r.wrong_count, "is_mastered": False}
        for r in wrong_records_db
    ]

    # 生成任务
    service = TaskGenerationService()
    task = service.generate(question_pool=q_pool, wrong_records=wrong_records, target_count=20)

    if not task.questions:
        raise HTTPException(
            status_code=404,
            detail="题目池为空，请家长前往【题库管理】页面添加练习题目后再开始"
        )

    # 创建DailyMission
    mission = DailyMission(
        child_id=child_id,
        mission_date=today,
        total_questions=len(task.questions),
    )
    db.add(mission)
    db.flush()

    for idx, q_data in enumerate(task.questions):
        mq = MissionQuestion(
            mission_id=mission.id,
            question_id=q_data["id"],
            order_index=idx,
            question_category=q_data.get("category", "basic"),
        )
        db.add(mq)

    db.commit()
    db.refresh(mission)
    return _format_mission(mission, db)


@router.post("/answer", summary="提交答案")
def submit_answer(
    data: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    mq = db.query(MissionQuestion).filter(MissionQuestion.id == data.mission_question_id).first()
    if not mq:
        raise HTTPException(status_code=404, detail="题目不存在")

    question = db.query(ParsedQuestion).filter(ParsedQuestion.id == mq.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目数据丢失")

    # 判分
    score = ScoringService.check_answer(question.normalized_text, data.submitted_answer)

    # 获取mission的child_id
    mission = db.query(DailyMission).filter(DailyMission.id == mq.mission_id).first()
    child_id = mission.child_id

    # 记录答题
    record = AnswerRecord(
        mission_question_id=mq.id,
        child_id=child_id,
        question_id=question.id,
        submitted_answer=data.submitted_answer,
        is_correct=score.is_correct,
        attempt_number=data.attempt,
    )
    db.add(record)

    # 更新MissionQuestion状态
    if not mq.is_answered or score.is_correct:
        mq.is_answered = True
        mq.is_correct = score.is_correct

    # 更新DailyMission统计
    if score.is_correct and not mq.is_correct:
        mission.correct_count += 1
    db.flush()  # 确保 mq.is_answered 写入连接，count() 才能正确计数
    mission.completed_questions = db.query(MissionQuestion).filter(
        MissionQuestion.mission_id == mission.id,
        MissionQuestion.is_answered == True
    ).count()

    # 检查任务是否完成
    if mission.completed_questions >= mission.total_questions:
        mission.is_completed = True
        mission.completed_at = datetime.utcnow()
        _update_streak(child_id, db)

    # 更新错题记录
    if not score.is_correct:
        _update_wrong_record(child_id, question.id, db)

    db.commit()

    # 生成反馈
    feedback = FeedbackService.generate_feedback(
        is_correct=score.is_correct,
        attempt=data.attempt,
        question_text=question.normalized_text,
    )

    return {
        "is_correct": score.is_correct,
        "correct_answer": score.correct_answer if not score.is_correct else None,
        "feedback": {
            "message": feedback.message,
            "show_answer": feedback.show_answer,
            "can_retry": feedback.can_retry,
            "show_explanation": feedback.show_explanation,
            "show_story_advance": feedback.show_story_advance,
            "hint": feedback.hint,
        },
        "mission_progress": {
            "completed": mission.completed_questions,
            "total": mission.total_questions,
            "is_completed": mission.is_completed,
        }
    }


@router.get("/{child_id}/today/status", summary="今日任务完成状态")
def get_today_status(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    mission = db.query(DailyMission).filter(
        DailyMission.child_id == child_id,
        DailyMission.mission_date == today
    ).first()

    if not mission:
        return {"has_mission": False, "is_completed": False}

    return {
        "has_mission": True,
        "mission_id": mission.id,
        "is_completed": mission.is_completed,
        "completed_questions": mission.completed_questions,
        "total_questions": mission.total_questions,
        "accuracy_rate": mission.accuracy_rate,
    }


def _format_mission(mission: DailyMission, db: Session) -> dict:
    """格式化任务数据"""
    mission_questions = db.query(MissionQuestion).filter(
        MissionQuestion.mission_id == mission.id
    ).order_by(MissionQuestion.order_index).all()

    questions_data = []
    for mq in mission_questions:
        q = db.query(ParsedQuestion).filter(ParsedQuestion.id == mq.question_id).first()
        if q:
            questions_data.append({
                "mission_question_id": mq.id,
                "question_id": q.id,
                "text": q.normalized_text,
                "question_type": q.question_type,
                "knowledge_tag": q.knowledge_tag,
                "category": mq.question_category,
                "is_answered": mq.is_answered,
                "is_correct": mq.is_correct,
            })

    return {
        "mission_id": mission.id,
        "mission_date": str(mission.mission_date),
        "total_questions": mission.total_questions,
        "completed_questions": mission.completed_questions,
        "is_completed": mission.is_completed,
        "questions": questions_data,
    }


def _update_wrong_record(child_id: int, question_id: int, db: Session):
    """更新错题记录"""
    wrong = db.query(WrongQuestionRecord).filter(
        WrongQuestionRecord.child_id == child_id,
        WrongQuestionRecord.question_id == question_id,
    ).first()

    if wrong:
        wrong.wrong_count += 1
        wrong.last_wrong_at = datetime.utcnow()
    else:
        wrong = WrongQuestionRecord(
            child_id=child_id,
            question_id=question_id,
            wrong_count=1,
        )
        db.add(wrong)


def _update_streak(child_id: int, db: Session):
    """更新连续打卡"""
    today = date.today()
    streak = db.query(StreakRecord).filter(StreakRecord.child_id == child_id).first()
    if not streak:
        streak = StreakRecord(child_id=child_id)
        db.add(streak)

    from datetime import timedelta
    yesterday = today - timedelta(days=1)
    if streak.last_checkin_date == yesterday:
        streak.current_streak += 1
    elif streak.last_checkin_date != today:
        streak.current_streak = 1

    streak.last_checkin_date = today
    streak.total_checkins += 1
    if streak.current_streak > streak.max_streak:
        streak.max_streak = streak.current_streak
