"""
用户相关数据模型
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, PyEnum):
    PARENT = "parent"
    CHILD = "child"


class User(Base):
    """用户账号基础表（家长/孩子共用登录账号）"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # 关联
    parent_profile = relationship("Parent", back_populates="user", uselist=False)
    child_profile = relationship("Child", back_populates="user", uselist=False)


class Parent(Base):
    """家长档案"""
    __tablename__ = "parents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    nickname = Column(String(50))

    user = relationship("User", back_populates="parent_profile")
    children = relationship("Child", back_populates="parent")


class Child(Base):
    """孩子档案"""
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    parent_id = Column(Integer, ForeignKey("parents.id"))
    nickname = Column(String(50), nullable=False)
    grade = Column(Integer, default=2)  # 年级，默认二年级
    avatar = Column(String(200), default="default")

    user = relationship("User", back_populates="child_profile")
    parent = relationship("Parent", back_populates="children")
    missions = relationship("DailyMission", back_populates="child")
    story_progress = relationship("ChildStoryProgress", back_populates="child")
    streak_record = relationship("StreakRecord", back_populates="child", uselist=False)
