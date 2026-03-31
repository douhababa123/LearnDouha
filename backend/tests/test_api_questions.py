"""
TDD: 题目管理 API 测试
覆盖：创建题目（自动识别知识点）、批量创建、列表、类似题、文件解析（PDF/图片）
"""
import pytest
from unittest.mock import patch


class TestCreateQuestion:
    def test_create_addition_question(self, client, parent_token):
        """创建加法题，自动识别知识点"""
        _, headers = parent_token
        resp = client.post("/api/questions/", json={
            "original_text": "23 + 45 = ___",
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "question_id" in data
        assert "add" in data["knowledge_tag"]   # add_no_carry 或 add_with_carry
        assert data["question_type"] in ("oral_calc", "fill_blank")  # 口算题或填空题均可
        assert data["correct_answer"] == "68"

    def test_create_unit_convert_question(self, client, parent_token):
        """创建单位换算题"""
        _, headers = parent_token
        resp = client.post("/api/questions/", json={
            "original_text": "2米 = ___厘米",
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["knowledge_tag"] == "unit_conversion"
        assert data["question_type"] == "unit_convert"

    def test_create_multiplication_question(self, client, parent_token):
        """创建乘法题，正确答案自动计算"""
        _, headers = parent_token
        resp = client.post("/api/questions/", json={
            "original_text": "6 × 7 = ___",
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["knowledge_tag"] == "multiply_table"
        assert data["correct_answer"] == "42"

    def test_create_question_no_auth(self, client):
        """未认证不能创建题目"""
        resp = client.post("/api/questions/", json={"original_text": "1 + 1 = ___"})
        assert resp.status_code == 401


class TestBatchCreate:
    def test_batch_create_success(self, client, parent_token):
        """批量创建 5 道题"""
        _, headers = parent_token
        questions = [
            {"original_text": f"1{i} + 2{i} = ___"} for i in range(5)
        ]
        resp = client.post("/api/questions/batch", json={"questions": questions}, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["created_count"] == 5
        assert len(data["questions"]) == 5

    def test_batch_create_returns_knowledge_tag(self, client, parent_token):
        """批量创建时每道题返回 knowledge_tag"""
        _, headers = parent_token
        resp = client.post("/api/questions/batch", json={
            "questions": [{"original_text": "9 × 8 = ___"}]
        }, headers=headers)
        assert resp.status_code == 200
        q = resp.json()["questions"][0]
        assert "knowledge_tag" in q

    def test_batch_create_with_wrong_field_name_returns_422(self, client, parent_token):
        """
        回归测试：payload 字段是 'text' 而非 'original_text' 时后端返回 422
        （这是 QuestionsPage.jsx 曾有的 Bug——字段名用错导致导入静默失败）
        """
        _, headers = parent_token
        resp = client.post("/api/questions/batch", json={
            "questions": [{"text": "9 + 8 = ___"}]   # ← 错误字段名
        }, headers=headers)
        assert resp.status_code == 422, (
            "字段名 'text' 应被后端拒绝（422），"
            "说明前端必须使用 'original_text'"
        )

    def test_batch_create_correct_field_name_succeeds(self, client, parent_token):
        """使用正确字段名 'original_text' 时批量导入成功"""
        _, headers = parent_token
        resp = client.post("/api/questions/batch", json={
            "questions": [{"original_text": "9 + 8 = ___"}]
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["created_count"] == 1


class TestListQuestions:
    def test_list_empty(self, client, parent_token):
        """新数据库题目列表为空"""
        _, headers = parent_token
        resp = client.get("/api/questions/", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        # 可能是 list 或 {questions: [...]}
        items = body if isinstance(body, list) else body.get("questions", body)
        assert len(items) == 0

    def test_list_after_create(self, client, parent_token):
        """创建 3 道题后列表有 3 条"""
        _, headers = parent_token
        for i in range(3):
            client.post("/api/questions/", json={"original_text": f"{i+1}0 + 1 = ___"}, headers=headers)
        resp = client.get("/api/questions/", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        items = body if isinstance(body, list) else body.get("questions", body)
        assert len(items) == 3


class TestSimilarQuestions:
    def test_get_similar_questions(self, client, parent_token):
        """获取某题的类似题（同知识点），至多返回 3 道"""
        _, headers = parent_token
        # 先批量创建足够的同类题
        questions = [{"original_text": f"1{i} + 2{i} = ___"} for i in range(10)]
        batch = client.post("/api/questions/batch", json={"questions": questions}, headers=headers)
        first_id = batch.json()["questions"][0]["question_id"]

        resp = client.get(f"/api/questions/{first_id}/similar", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        # 返回的类似题不超过 3 道，且不包含自身
        similar = data if isinstance(data, list) else data.get("similar_questions", [])
        assert len(similar) <= 3
        ids = [q.get("question_id") or q.get("id") for q in similar]
        assert first_id not in ids

    def test_similar_questions_no_auth(self, client):
        """未认证不能获取类似题"""
        resp = client.get("/api/questions/999/similar")
        assert resp.status_code == 401


class TestParseFile:
    """TDD: 从 PDF / 图片文件中解析题目行"""

    def test_parse_file_no_auth_returns_401(self, client):
        """未认证不能使用文件解析接口"""
        resp = client.post(
            "/api/questions/parse-file",
            files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert resp.status_code == 401

    def test_parse_file_wrong_type_returns_400(self, client, parent_token):
        """不支持的文件格式（.exe）应返回 400"""
        _, headers = parent_token
        resp = client.post(
            "/api/questions/parse-file",
            files={"file": ("malware.exe", b"fake", "application/octet-stream")},
            headers=headers,
        )
        assert resp.status_code == 400
        assert "不支持" in resp.json()["detail"]

    def test_parse_file_pdf_returns_lines(self, client, parent_token):
        """上传 PDF 返回解析后的题目行（mock OCR 服务）"""
        _, headers = parent_token
        with patch("app.services.ocr_service.extract_from_pdf") as mock_fn:
            mock_fn.return_value = (["24 + 37 = ___", "63 - 28 = ___"], "pdf_text")
            resp = client.post(
                "/api/questions/parse-file",
                files={"file": ("worksheet.pdf", b"%PDF-1.4", "application/pdf")},
                headers=headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["method"] == "pdf_text"
        assert "24 + 37 = ___" in data["lines"]

    def test_parse_file_image_returns_lines(self, client, parent_token):
        """上传图片返回 OCR 识别结果（mock OCR 服务）"""
        _, headers = parent_token
        with patch("app.services.ocr_service.extract_from_image") as mock_fn:
            mock_fn.return_value = (["5 × 6 = ___", "8 × 7 = ___", "9 - 4 = ___"], "ocr")
            resp = client.post(
                "/api/questions/parse-file",
                files={"file": ("photo.png", b"\x89PNG\r\n", "image/png")},
                headers=headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3
        assert data["method"] == "ocr"
        assert "5 × 6 = ___" in data["lines"]

    def test_parse_file_empty_result_returns_422(self, client, parent_token):
        """文件中无法识别任何题目时返回 422"""
        _, headers = parent_token
        with patch("app.services.ocr_service.extract_from_pdf") as mock_fn:
            mock_fn.return_value = ([], "pdf_text")
            resp = client.post(
                "/api/questions/parse-file",
                files={"file": ("blank.pdf", b"%PDF-1.4", "application/pdf")},
                headers=headers,
            )
        assert resp.status_code == 422
        assert "未能" in resp.json()["detail"]

    def test_parse_file_ocr_lib_not_installed_returns_503(self, client, parent_token):
        """easyocr 未安装时返回 503 及安装提示"""
        _, headers = parent_token
        with patch(
            "app.services.ocr_service.extract_from_image",
            side_effect=ImportError("easyocr 未安装，请运行 pip install easyocr"),
        ):
            resp = client.post(
                "/api/questions/parse-file",
                files={"file": ("sheet.jpg", b"\xff\xd8\xff", "image/jpeg")},
                headers=headers,
            )
        assert resp.status_code == 503

    def test_parse_file_jpg_extension_supported(self, client, parent_token):
        """jpg / jpeg 扩展名都应被支持"""
        _, headers = parent_token
        for ext in ["jpg", "jpeg"]:
            with patch("app.services.ocr_service.extract_from_image") as mock_fn:
                mock_fn.return_value = (["1 + 1 = ___"], "ocr")
                resp = client.post(
                    "/api/questions/parse-file",
                    files={"file": (f"test.{ext}", b"\xff\xd8", "image/jpeg")},
                    headers=headers,
                )
            assert resp.status_code == 200, f".{ext} 应被支持"


class TestParseQuestionLines:
    """TDD: parse_question_lines 纯函数单元测试"""

    def test_filters_empty_lines(self):
        from app.services.ocr_service import parse_question_lines
        result = parse_question_lines("24 + 37 = ___\n\n63 - 28 = ___\n")
        assert result == ["24 + 37 = ___", "63 - 28 = ___"]

    def test_filters_too_short_lines(self):
        from app.services.ocr_service import parse_question_lines
        result = parse_question_lines("A\nAB\n24 + 37 = ___")
        assert result == ["24 + 37 = ___"]

    def test_filters_pure_number_lines(self):
        from app.services.ocr_service import parse_question_lines
        # 纯数字行通常是页码，应被过滤
        result = parse_question_lines("1\n24 + 37 = ___\n100")
        assert result == ["24 + 37 = ___"]

    def test_keeps_chinese_math_questions(self):
        from app.services.ocr_service import parse_question_lines
        text = "24 + 37 = ___\n5 × 6 = ___\n2米 = ___厘米"
        result = parse_question_lines(text)
        assert len(result) == 3

    def test_strips_whitespace(self):
        from app.services.ocr_service import parse_question_lines
        result = parse_question_lines("  24 + 37 = ___  \n\t63 - 28 = ___\t")
        assert result == ["24 + 37 = ___", "63 - 28 = ___"]


class TestParseFileWithAI:
    """TDD: 启用 DASHSCOPE_API_KEY 后使用通义千问 VL 模型识别"""

    def test_image_uses_ai_when_api_key_set(self, client, parent_token):
        """设置了 API Key 时，图片解析应调用 AI 接口"""
        _, headers = parent_token
        with patch("app.services.ocr_service.extract_from_image_with_ai") as mock_fn, \
             patch.dict("os.environ", {"DASHSCOPE_API_KEY": "sk-test"}):
            mock_fn.return_value = (["5 × 6 = ___", "8 × 7 = ___"], "qwen_vl")
            resp = client.post(
                "/api/questions/parse-file",
                files={"file": ("photo.jpg", b"\xff\xd8\xff", "image/jpeg")},
                headers=headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["method"] == "qwen_vl"
        assert data["count"] == 2
        mock_fn.assert_called_once()

    def test_pdf_uses_ai_when_pdfplumber_returns_empty(self, client, parent_token):
        """扫描 PDF（pdfplumber 提取为空）时应调用 AI"""
        _, headers = parent_token
        with patch("app.services.ocr_service.extract_from_pdf") as pdf_mock, \
             patch("app.services.ocr_service.extract_from_pdf_with_ai") as ai_mock, \
             patch.dict("os.environ", {"DASHSCOPE_API_KEY": "sk-test"}):
            pdf_mock.return_value = ([], "pdf_text")       # pdfplumber 无内容（扫描件）
            ai_mock.return_value = (["24 + 37 = ___"], "qwen_vl")
            resp = client.post(
                "/api/questions/parse-file",
                files={"file": ("scan.pdf", b"%PDF-1.4", "application/pdf")},
                headers=headers,
            )
        assert resp.status_code == 200
        assert resp.json()["method"] == "qwen_vl"
        ai_mock.assert_called_once()

    def test_pdf_uses_pdfplumber_when_text_available(self, client, parent_token):
        """数字 PDF（pdfplumber 有内容）时不应调用 AI，即使有 Key"""
        _, headers = parent_token
        with patch("app.services.ocr_service.extract_from_pdf") as pdf_mock, \
             patch("app.services.ocr_service.extract_from_pdf_with_ai") as ai_mock, \
             patch.dict("os.environ", {"DASHSCOPE_API_KEY": "sk-test"}):
            pdf_mock.return_value = (["24 + 37 = ___"], "pdf_text")   # 有内容
            resp = client.post(
                "/api/questions/parse-file",
                files={"file": ("digital.pdf", b"%PDF-1.4", "application/pdf")},
                headers=headers,
            )
        assert resp.status_code == 200
        assert resp.json()["method"] == "pdf_text"
        ai_mock.assert_not_called()   # AI 不应被调用

    def test_image_falls_back_to_local_when_no_api_key(self, client, parent_token):
        """没有 API Key 时，图片解析应使用本地 easyocr"""
        _, headers = parent_token
        with patch("app.services.ocr_service.extract_from_image") as local_mock, \
             patch.dict("os.environ", {"DASHSCOPE_API_KEY": ""}):
            local_mock.return_value = (["1 + 1 = ___"], "ocr")
            resp = client.post(
                "/api/questions/parse-file",
                files={"file": ("photo.png", b"\x89PNG", "image/png")},
                headers=headers,
            )
        assert resp.status_code == 200
        assert resp.json()["method"] == "ocr"

    def test_ai_api_error_returns_422(self, client, parent_token):
        """AI 接口调用失败时返回 422 含错误信息"""
        _, headers = parent_token
        with patch("app.services.ocr_service.extract_from_image_with_ai",
                   side_effect=Exception("API rate limit exceeded")), \
             patch.dict("os.environ", {"DASHSCOPE_API_KEY": "sk-test"}):
            resp = client.post(
                "/api/questions/parse-file",
                files={"file": ("photo.jpg", b"\xff\xd8", "image/jpeg")},
                headers=headers,
            )
        assert resp.status_code == 422
        assert "API rate limit" in resp.json()["detail"]


class TestParseConfig:
    """TDD: GET /parse-config 返回 AI 配置状态"""

    def test_parse_config_ai_enabled_when_key_set(self, client, parent_token):
        """配置了 API Key 时，ai_enabled 应为 True"""
        _, headers = parent_token
        with patch.dict("os.environ", {"DASHSCOPE_API_KEY": "sk-real-key"}):
            resp = client.get("/api/questions/parse-config", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ai_enabled"] is True
        assert data["ai_model"] == "qwen-vl-plus"
        assert "通义千问" in data["ai_provider"]

    def test_parse_config_ai_disabled_when_no_key(self, client, parent_token):
        """没有 API Key 时，ai_enabled 应为 False"""
        _, headers = parent_token
        with patch.dict("os.environ", {"DASHSCOPE_API_KEY": ""}):
            resp = client.get("/api/questions/parse-config", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ai_enabled"] is False
        assert data["ai_model"] is None
