"""
题目路由 - 题目管理、知识点识别、类似题生成
"""
import os
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import random

from app.database import get_db
from app.models.user import User
from app.models.question import ParsedQuestion, KnowledgeTag, QuestionType, DifficultyLevel
from app.routers.auth import get_current_user
from app.services.knowledge_service import KnowledgePointService
from app.services.scoring_service import ScoringService
from app.services import ocr_service
from app.services.ocr_service import _QWEN_VL_MODEL


def _get_ai_key() -> str:
    """读取通义千问 API Key（从环境变量或 .env 文件）"""
    return os.getenv("DASHSCOPE_API_KEY", "").strip()

router = APIRouter()


class CreateQuestionRequest(BaseModel):
    original_text: str
    correct_answer: Optional[str] = None


class BatchCreateRequest(BaseModel):
    questions: List[CreateQuestionRequest]


@router.post("/", summary="创建单道题目（含自动知识点识别）")
def create_question(
    data: CreateQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    analysis = KnowledgePointService.identify(data.original_text)

    # 自动计算正确答案（如果未提供）
    correct_answer = data.correct_answer
    if not correct_answer:
        score_result = ScoringService._compute_correct_answer(data.original_text)
        correct_answer = score_result or ""

    q = ParsedQuestion(
        original_text=data.original_text,
        normalized_text=analysis.normalized_text,
        question_type=analysis.question_type,
        knowledge_tag=analysis.knowledge_tag,
        difficulty=analysis.difficulty,
        correct_answer=correct_answer,
    )
    db.add(q)
    db.commit()
    db.refresh(q)

    return {
        "question_id": q.id,
        "normalized_text": q.normalized_text,
        "question_type": q.question_type,
        "knowledge_tag": q.knowledge_tag,
        "difficulty": q.difficulty,
        "correct_answer": q.correct_answer,
    }


@router.post("/batch", summary="批量创建题目")
def batch_create_questions(
    data: BatchCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    created = []
    for item in data.questions:
        analysis = KnowledgePointService.identify(item.original_text)
        correct_answer = item.correct_answer
        if not correct_answer:
            correct_answer = ScoringService._compute_correct_answer(item.original_text) or ""

        q = ParsedQuestion(
            original_text=item.original_text,
            normalized_text=analysis.normalized_text,
            question_type=analysis.question_type,
            knowledge_tag=analysis.knowledge_tag,
            difficulty=analysis.difficulty,
            correct_answer=correct_answer,
        )
        db.add(q)
        db.flush()
        created.append({"question_id": q.id, "text": q.normalized_text, "knowledge_tag": q.knowledge_tag})

    db.commit()
    return {"created_count": len(created), "questions": created}


# ─────────────────────────────────────────────────────────────
# 文件解析端点 — 从 PDF / 图片提取题目行（供前端预览后批量导入）
# ─────────────────────────────────────────────────────────────

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


@router.post("/parse-file", summary="从PDF或图片中解析题目行（不入库，仅返回预览）")
async def parse_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    上传 PDF 或图片，智能提取其中的题目文本行。

    策略：
    - 设置了 DASHSCOPE_API_KEY → 优先使用通义千问 VL 大模型（精度高）
      - PDF 含文字 → pdfplumber 直接提取（无需 AI，速度快）
      - PDF 扫描件 → 转图片后调用 AI 识别
      - 图片 → 直接调用 AI 识别
    - 未设置 API Key → 本地模型（pdfplumber / easyocr）兜底

    返回 {"lines": [...], "count": N, "method": "pdf_text"|"ocr"|"qwen_vl"}
    """
    api_key = _get_ai_key()
    use_ai = bool(api_key)

    filename = (file.filename or "").lower()
    ext = os.path.splitext(filename)[1]
    file_bytes = await file.read()

    if ext not in ({".pdf"} | _IMAGE_EXTS):
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式，请上传 PDF 或图片（JPG / PNG / WEBP）",
        )

    try:
        if ext == ".pdf":
            # 先用 pdfplumber 提取（数字 PDF，速度快）
            lines, method = ocr_service.extract_from_pdf(file_bytes)
            if not lines and use_ai:
                # 扫描件 PDF：转图片后调用通义千问 VL
                lines, method = ocr_service.extract_from_pdf_with_ai(file_bytes, api_key)
            elif not lines:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "未能从 PDF 中提取到文字（可能是扫描件）。"
                        "配置 DASHSCOPE_API_KEY 后可使用通义千问 VL 自动识别扫描件"
                    ),
                )
        else:  # 图片
            if use_ai:
                lines, method = ocr_service.extract_from_image_with_ai(file_bytes, api_key)
            else:
                lines, method = ocr_service.extract_from_image(file_bytes)

    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"文件解析失败：{e}")

    if not lines:
        raise HTTPException(
            status_code=422,
            detail="未能从文件中识别到题目内容，请检查文件是否清晰，或改用手动输入",
        )

    return {"lines": lines, "count": len(lines), "method": method}


@router.get("/parse-config", summary="获取文件解析配置（AI 是否可用）")
def get_parse_config(current_user: User = Depends(get_current_user)):
    """返回当前是否已配置通义千问 API Key，供前端展示状态。"""
    api_key = _get_ai_key()
    enabled = bool(api_key)
    return {
        "ai_enabled": enabled,
        "ai_model": _QWEN_VL_MODEL if enabled else None,
        "ai_provider": "阿里云通义千问" if enabled else None,
    }


@router.get("/{question_id}/similar", summary="获取同知识点类似题（3道）")
def get_similar_questions(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成3道同知识点的类似题（从题库中随机取，或生成新题）"""
    source = db.query(ParsedQuestion).filter(ParsedQuestion.id == question_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 从同知识点题库中随机取3道（排除自身）
    similar = db.query(ParsedQuestion).filter(
        ParsedQuestion.knowledge_tag == source.knowledge_tag,
        ParsedQuestion.id != question_id,
        ParsedQuestion.is_usable == True,
    ).all()

    if len(similar) >= 3:
        chosen = random.sample(similar, 3)
    else:
        # 不足3道时，全部返回
        chosen = similar

    return {
        "knowledge_tag": source.knowledge_tag,
        "source_question": source.normalized_text,
        "similar_questions": [
            {
                "question_id": q.id,
                "text": q.normalized_text,
                "knowledge_tag": q.knowledge_tag,
            }
            for q in chosen
        ],
    }


@router.get("/", summary="获取题目列表")
def list_questions(
    knowledge_tag: Optional[str] = None,
    question_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ParsedQuestion).filter(ParsedQuestion.is_usable == True)
    if knowledge_tag:
        query = query.filter(ParsedQuestion.knowledge_tag == knowledge_tag)
    if question_type:
        query = query.filter(ParsedQuestion.question_type == question_type)

    questions = query.limit(100).all()
    return [
        {
            "question_id": q.id,
            "text": q.normalized_text,
            "question_type": q.question_type,
            "knowledge_tag": q.knowledge_tag,
            "difficulty": q.difficulty,
        }
        for q in questions
    ]
