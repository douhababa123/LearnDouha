"""
题目相关数据模型
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class QuestionType(str, PyEnum):
    ORAL_CALC = "oral_calc"          # 口算题
    VERTICAL_CALC = "vertical_calc"  # 竖式计算
    MIXED_CALC = "mixed_calc"        # 脱式计算
    FILL_BLANK = "fill_blank"        # 填空题
    UNIT_CONVERT = "unit_convert"    # 单位换算
    WORD_PROBLEM = "word_problem"    # 应用题


class KnowledgeTag(str, PyEnum):
    ADD_NO_CARRY = "add_no_carry"            # 100以内不进位加法
    ADD_WITH_CARRY = "add_with_carry"        # 100以内进位加法
    SUB_NO_BORROW = "sub_no_borrow"          # 100以内不退位减法
    SUB_WITH_BORROW = "sub_with_borrow"      # 100以内退位减法
    MULTIPLY_TABLE = "multiply_table"        # 表内乘法
    UNIT_CONVERSION = "unit_conversion"      # 单位换算
    MIXED_OPERATION = "mixed_operation"      # 混合运算
    WORD_PROBLEM = "word_problem"            # 应用题


class DifficultyLevel(int, PyEnum):
    EASY = 1
    MEDIUM = 2
    HARD = 3


class SourceDocument(Base):
    """原始PDF文档"""
    __tablename__ = "source_documents"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    parse_status = Column(String(20), default="pending")  # pending/processing/done/failed
    created_at = Column(DateTime, default=datetime.utcnow)
    parsed_at = Column(DateTime, nullable=True)

    questions = relationship("ParsedQuestion", back_populates="source_doc")


class ParsedQuestion(Base):
    """解析后的题目"""
    __tablename__ = "parsed_questions"

    id = Column(Integer, primary_key=True, index=True)
    source_doc_id = Column(Integer, ForeignKey("source_documents.id"), nullable=True)
    original_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    knowledge_tag = Column(Enum(KnowledgeTag), nullable=False)
    difficulty = Column(Integer, default=DifficultyLevel.EASY)
    correct_answer = Column(String(100), nullable=False)
    display_format = Column(String(50), default="text")  # text/vertical
    is_usable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    source_doc = relationship("SourceDocument", back_populates="questions")
    mission_questions = relationship("MissionQuestion", back_populates="question")
