"""
孩子端路由 - 孩子信息、打卡进度
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import Child, Parent, User
from app.models.learning import StreakRecord
from app.routers.auth import get_current_user
from datetime import date

router = APIRouter()


class CreateChildRequest(BaseModel):
    nickname: str
    grade: int = 2
    avatar: str = "default"


@router.post("/", summary="家长创建孩子账号")
def create_child(
    data: CreateChildRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    if not parent:
        raise HTTPException(status_code=403, detail="只有家长可以创建孩子账号")

    child = Child(
        user_id=None,  # 孩子可以没有独立账号（由家长代操作）
        parent_id=parent.id,
        nickname=data.nickname,
        grade=data.grade,
        avatar=data.avatar,
    )
    db.add(child)
    db.flush()

    # 初始化连续打卡记录
    streak = StreakRecord(child_id=child.id)
    db.add(streak)

    db.commit()
    db.refresh(child)
    return {"child_id": child.id, "nickname": child.nickname, "grade": child.grade}


@router.get("/", summary="获取家长名下的孩子列表")
def list_children(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    parent = db.query(Parent).filter(Parent.user_id == current_user.id).first()
    if not parent:
        raise HTTPException(status_code=403, detail="只有家长可以查看孩子列表")

    children = db.query(Child).filter(Child.parent_id == parent.id).all()
    return [
        {
            "child_id": c.id,
            "nickname": c.nickname,
            "grade": c.grade,
            "avatar": c.avatar,
        }
        for c in children
    ]


@router.get("/{child_id}/streak", summary="获取孩子连续打卡记录")
def get_streak(
    child_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    streak = db.query(StreakRecord).filter(StreakRecord.child_id == child_id).first()
    if not streak:
        return {"current_streak": 0, "max_streak": 0, "total_checkins": 0}
    return {
        "current_streak": streak.current_streak,
        "max_streak": streak.max_streak,
        "total_checkins": streak.total_checkins,
        "last_checkin_date": str(streak.last_checkin_date) if streak.last_checkin_date else None,
    }
