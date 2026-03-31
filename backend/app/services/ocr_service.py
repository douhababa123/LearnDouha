"""
OCR 服务 — 从 PDF 和图片文件中提取题目文本

PDF（含文字）: pdfplumber  →  直接提取文本，速度快
图片 / 扫描 PDF: easyocr   →  本地深度学习 OCR，支持中英文混排（无 API Key 时的兜底）
图片 / 扫描 PDF: 通义千问 VL →  阿里云大模型，理解力强，精度高（推荐，需 DASHSCOPE_API_KEY）
"""
import io
import re
from typing import List, Tuple


# ─────────────────────────────────────────────────────────────
# 公共工具
# ─────────────────────────────────────────────────────────────

def parse_question_lines(text: str) -> List[str]:
    """
    从 OCR / LLM 返回的原始文本中筛选出题目行。

    过滤规则：
    1. 去除空行
    2. 去除长度 < 3 的行（孤立标点、字母等）
    3. 去除纯数字行（通常是页码）
    """
    lines: List[str] = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if len(line) < 3:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        lines.append(line)
    return lines


# ─────────────────────────────────────────────────────────────
# PDF 提取（pdfplumber）
# ─────────────────────────────────────────────────────────────

def extract_from_pdf(file_bytes: bytes) -> Tuple[List[str], str]:
    """
    从含嵌入文字的 PDF 中提取题目行。

    返回 (lines, "pdf_text")。
    若 pdfplumber 未安装，抛出 ImportError（调用方转为 503）。
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "PDF 解析库未安装，请运行：pip install pdfplumber"
        )

    parts: List[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)

    full_text = "\n".join(parts)
    lines = parse_question_lines(full_text)
    return lines, "pdf_text"


# ─────────────────────────────────────────────────────────────
# 图片本地 OCR（easyocr + Pillow）
# ─────────────────────────────────────────────────────────────

def extract_from_image(file_bytes: bytes) -> Tuple[List[str], str]:
    """
    对图片文件做本地 OCR，支持中文 + 英文混排（适合数学题）。

    返回 (lines, "ocr")。
    首次运行会下载模型（~400 MB），之后缓存到本地。
    若 easyocr 或 Pillow 未安装，抛出 ImportError（调用方转为 503）。
    """
    try:
        import easyocr
    except ImportError:
        raise ImportError(
            "OCR 库未安装，请运行：pip install easyocr"
        )
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        raise ImportError(
            "图像处理库未安装，请运行：pip install Pillow numpy"
        )

    # 初始化 Reader（支持简体中文 + 英文）
    # verbose=False 避免打印进度条
    reader = easyocr.Reader(["ch_sim", "en"], verbose=False)

    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    image_np = np.array(image)

    # detail=0 只返回文本字符串，paragraph=False 保留逐行结果
    results: List[str] = reader.readtext(image_np, detail=0, paragraph=False)

    full_text = "\n".join(str(r) for r in results)
    lines = parse_question_lines(full_text)
    return lines, "ocr"


# ─────────────────────────────────────────────────────────────
# 通义千问 VL 大模型识别（高精度，需 DASHSCOPE_API_KEY）
# ─────────────────────────────────────────────────────────────

_QWEN_VL_MODEL = "qwen-vl-plus"

_MATH_EXTRACTION_PROMPT = (
    "请识别图片中的所有数学题目，每道题单独占一行输出。\n"
    "输出要求：\n"
    "1. 只输出题目本身，每行一道题\n"
    "2. 不要编号（如1. 2. 一、）\n"
    "3. 不要任何解释文字\n"
    "4. 空白处用 ___ 表示\n"
    "5. 若图中没有数学题目，只输出：无\n"
    "示例格式：\n"
    "24 + 37 = ___\n"
    "63 - 28 = ___\n"
    "5 × 6 = ___\n"
    "2米 = ___厘米"
)


def _call_qwen_vl(img_bytes: bytes, api_key: str) -> List[str]:
    """
    调用通义千问 VL 模型识别图片中的数学题目。
    使用 DashScope 的 OpenAI 兼容接口。
    """
    import base64

    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI SDK 未安装，请运行：pip install openai"
        )

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    b64 = base64.b64encode(img_bytes).decode()

    response = client.chat.completions.create(
        model=_QWEN_VL_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                },
                {"type": "text", "text": _MATH_EXTRACTION_PROMPT},
            ],
        }],
    )

    text = (response.choices[0].message.content or "").strip()

    # 模型回答"无"说明图片中没有题目
    if text in ("无", "无题目", "无数学题目", "无内容"):
        return []

    return parse_question_lines(text)


def extract_from_image_with_ai(file_bytes: bytes, api_key: str) -> Tuple[List[str], str]:
    """
    用通义千问 VL 模型识别图片中的数学题目。
    返回 (lines, "qwen_vl")。
    """
    lines = _call_qwen_vl(file_bytes, api_key)
    return lines, "qwen_vl"


def extract_from_pdf_with_ai(file_bytes: bytes, api_key: str) -> Tuple[List[str], str]:
    """
    将扫描 PDF 的每页渲染为图片，再调用通义千问 VL 识别题目。
    仅在 pdfplumber 无法提取文字（扫描件）时使用。
    返回 (lines, "qwen_vl")。
    需要 PyMuPDF（pymupdf）：pip install pymupdf
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PDF 渲染库未安装，请运行：pip install pymupdf"
        )

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    all_lines: List[str] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        mat = fitz.Matrix(2.0, 2.0)   # 2× 缩放，提升识别精度
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        page_lines = _call_qwen_vl(img_bytes, api_key)
        all_lines.extend(page_lines)

    # 跨页去重（保持顺序）
    seen: set = set()
    unique_lines: List[str] = []
    for line in all_lines:
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)

    return unique_lines, "qwen_vl"



# ─────────────────────────────────────────────────────────────
# 公共工具
# ─────────────────────────────────────────────────────────────

def parse_question_lines(text: str) -> List[str]:
    """
    从 OCR / PDF 提取到的原始文本中筛选出题目行。

    过滤规则：
    1. 去除空行
    2. 去除长度 < 3 的行（孤立标点、字母等）
    3. 去除纯数字行（通常是页码）
    """
    lines: List[str] = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if len(line) < 3:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        lines.append(line)
    return lines


# ─────────────────────────────────────────────────────────────
# PDF 提取（pdfplumber）
# ─────────────────────────────────────────────────────────────

def extract_from_pdf(file_bytes: bytes) -> Tuple[List[str], str]:
    """
    从含嵌入文字的 PDF 中提取题目行。

    返回 (lines, "pdf_text")。
    若 pdfplumber 未安装，抛出 ImportError（调用方转为 503）。
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "PDF 解析库未安装，请运行：pip install pdfplumber"
        )

    parts: List[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)

    full_text = "\n".join(parts)
    lines = parse_question_lines(full_text)
    return lines, "pdf_text"


# ─────────────────────────────────────────────────────────────
# 图片 OCR（easyocr + Pillow）
# ─────────────────────────────────────────────────────────────

def extract_from_image(file_bytes: bytes) -> Tuple[List[str], str]:
    """
    对图片文件做 OCR，支持中文 + 英文混排（适合数学题）。

    返回 (lines, "ocr")。
    首次运行会下载模型（~400 MB），之后缓存到本地。
    若 easyocr 或 Pillow 未安装，抛出 ImportError（调用方转为 503）。
    """
    try:
        import easyocr
    except ImportError:
        raise ImportError(
            "OCR 库未安装，请运行：pip install easyocr"
        )
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        raise ImportError(
            "图像处理库未安装，请运行：pip install Pillow numpy"
        )

    # 初始化 Reader（支持简体中文 + 英文）
    # verbose=False 避免打印进度条
    reader = easyocr.Reader(["ch_sim", "en"], verbose=False)

    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    image_np = np.array(image)

    # detail=0 只返回文本字符串，paragraph=False 保留逐行结果
    results: List[str] = reader.readtext(image_np, detail=0, paragraph=False)

    full_text = "\n".join(str(r) for r in results)
    lines = parse_question_lines(full_text)
    return lines, "ocr"
