"""
剧情系统数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base


class StoryLine(Base):
    """剧情主线"""
    __tablename__ = "story_lines"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    total_chapters = Column(Integer, default=7)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chapters = relationship("StoryChapter", back_populates="story_line")


class StoryChapter(Base):
    """剧情章节"""
    __tablename__ = "story_chapters"

    id = Column(Integer, primary_key=True, index=True)
    story_line_id = Column(Integer, ForeignKey("story_lines.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(100), nullable=False)
    intro_text = Column(Text)           # 章节开始剧情文案
    reward_text = Column(Text)          # 通关奖励文案
    unlock_condition = Column(Text)     # 解锁条件（JSON）
    image_key = Column(String(100))     # 插图资源key

    story_line = relationship("StoryLine", back_populates="chapters")
    missions = relationship("DailyMission", back_populates="story_chapter")
    child_progress = relationship("ChildStoryProgress", back_populates="chapter")


class ChildStoryProgress(Base):
    """孩子剧情进度"""
    __tablename__ = "child_story_progress"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    story_line_id = Column(Integer, ForeignKey("story_lines.id"), nullable=False)
    current_chapter_id = Column(Integer, ForeignKey("story_chapters.id"), nullable=True)
    completed_chapters = Column(Integer, default=0)
    unlocked_at = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

    child = relationship("Child", back_populates="story_progress")
    chapter = relationship("StoryChapter", back_populates="child_progress")
