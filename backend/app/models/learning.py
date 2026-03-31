"""
学习记录相关数据模型
"""
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Boolean, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base


class MasteryLevel(str, PyEnum):
    NOT_STARTED = "not_started"   # 未开始
    LEARNING = "learning"         # 学习中
    INITIAL = "initial"           # 初步掌握
    MASTERED = "mastered"         # 已掌握


class DailyMission(Base):
    """每日任务"""
    __tablename__ = "daily_missions"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    mission_date = Column(Date, nullable=False)
    total_questions = Column(Integer, default=0)
    completed_questions = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    story_chapter_id = Column(Integer, ForeignKey("story_chapters.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    child = relationship("Child", back_populates="missions")
    questions = relationship("MissionQuestion", back_populates="mission")
    story_chapter = relationship("StoryChapter", back_populates="missions")

    @property
    def accuracy_rate(self) -> float:
        """正确率"""
        if self.completed_questions == 0:
            return 0.0
        return round(self.correct_count / self.completed_questions, 4)


class MissionQuestion(Base):
    """每日任务中的题目"""
    __tablename__ = "mission_questions"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("daily_missions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("parsed_questions.id"), nullable=False)
    order_index = Column(Integer, default=0)
    question_category = Column(String(20), default="basic")  # basic/review/wrong_recycle/story
    is_answered = Column(Boolean, default=False)
    is_correct = Column(Boolean, nullable=True)

    mission = relationship("DailyMission", back_populates="questions")
    question = relationship("ParsedQuestion", back_populates="mission_questions")
    answer_records = relationship("AnswerRecord", back_populates="mission_question")


class AnswerRecord(Base):
    """答题记录"""
    __tablename__ = "answer_records"

    id = Column(Integer, primary_key=True, index=True)
    mission_question_id = Column(Integer, ForeignKey("mission_questions.id"), nullable=False)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("parsed_questions.id"), nullable=False)
    submitted_answer = Column(String(200), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    attempt_number = Column(Integer, default=1)   # 第几次尝试
    answered_at = Column(DateTime, default=datetime.utcnow)

    mission_question = relationship("MissionQuestion", back_populates="answer_records")


class WrongQuestionRecord(Base):
    """错题记录"""
    __tablename__ = "wrong_question_records"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("parsed_questions.id"), nullable=False)
    wrong_count = Column(Integer, default=1)
    last_wrong_at = Column(DateTime, default=datetime.utcnow)
    is_reinforced = Column(Boolean, default=False)  # 是否已强化
    is_mastered = Column(Boolean, default=False)     # 是否已掌握


class MasteryRecord(Base):
    """知识点掌握记录"""
    __tablename__ = "mastery_records"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    knowledge_tag = Column(String(50), nullable=False)
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    mastery_level = Column(String(20), default=MasteryLevel.NOT_STARTED)
    last_updated = Column(DateTime, default=datetime.utcnow)

    @property
    def error_rate(self) -> float:
        """错误率"""
        if self.total_attempts == 0:
            return 0.0
        return round(1 - self.correct_attempts / self.total_attempts, 4)


class StreakRecord(Base):
    """连续打卡记录"""
    __tablename__ = "streak_records"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), unique=True, nullable=False)
    current_streak = Column(Integer, default=0)    # 当前连续天数
    max_streak = Column(Integer, default=0)        # 历史最大连续天数
    last_checkin_date = Column(Date, nullable=True)
    total_checkins = Column(Integer, default=0)

    child = relationship("Child", back_populates="streak_record")


class WeeklyReport(Base):
    """每周学习报告"""
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    total_questions = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    avg_accuracy = Column(Float, default=0.0)
    completion_days = Column(Integer, default=0)
    top_weak_points = Column(Text, default="[]")  # JSON list
    top_progress_points = Column(Text, default="[]")  # JSON list
    ai_summary = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
