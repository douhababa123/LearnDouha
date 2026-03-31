/* =============================================
   API Client — 封装所有后端请求
   ============================================= */

const BASE = '/api'

function getToken() {
  return localStorage.getItem('token')
}

async function request(path, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  }
  const res = await fetch(`${BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || '请求失败')
  }
  return res.json()
}

// ——— 认证 ———
export const auth = {
  async login(username, password) {
    const form = new URLSearchParams({ username, password })
    const res = await fetch(`${BASE}/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    })
    if (!res.ok) throw new Error('用户名或密码错误')
    return res.json()
  },

  async register(username, password, role, nickname) {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, role, nickname }),
    })
  },

  async getMe() {
    return request('/auth/me')
  },

  logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('userId')
  },
}

// ——— 孩子管理 ———
export const children = {
  async list() {
    return request('/children/')
  },
  async create(nickname, grade = 2) {
    return request('/children/', {
      method: 'POST',
      body: JSON.stringify({ nickname, grade }),
    })
  },
  async getStreak(childId) {
    return request(`/children/${childId}/streak`)
  },
}

// ——— 每日任务 ———
export const missions = {
  async getOrCreate(childId) {
    return request(`/missions/${childId}/today`, { method: 'POST' })
  },
  async getTodayStatus(childId) {
    return request(`/missions/${childId}/today/status`)
  },
  async submitAnswer(missionQuestionId, submittedAnswer, attempt = 1) {
    return request('/missions/answer', {
      method: 'POST',
      body: JSON.stringify({ mission_question_id: missionQuestionId, submitted_answer: submittedAnswer, attempt }),
    })
  },
}

// ——— 题目管理 ———
export const questions = {
  async list(params = {}) {
    const q = new URLSearchParams(params).toString()
    return request(`/questions/${q ? '?' + q : ''}`)
  },
  async create(originalText, correctAnswer = '') {
    return request('/questions/', {
      method: 'POST',
      body: JSON.stringify({ original_text: originalText, correct_answer: correctAnswer }),
    })
  },
  async batchCreate(items) {
    return request('/questions/batch', {
      method: 'POST',
      body: JSON.stringify({ questions: items }),
    })
  },
  async getSimilar(questionId) {
    return request(`/questions/${questionId}/similar`)
  },
  /**
   * 上传 PDF 或图片，解析其中的题目行（不入库，仅返回预览）
   * 返回 { lines: string[], count: number, method: 'pdf_text' | 'ocr' | 'qwen_vl' }
   */
  async parseFile(file) {
    const token = getToken()
    const formData = new FormData()
    formData.append('file', file)
    // 注意：不手动设置 Content-Type，让浏览器自动加 multipart boundary
    const res = await fetch(`${BASE}/questions/parse-file`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || '文件解析失败')
    }
    return res.json()
  },
  /**
   * 获取文件解析配置（AI 是否可用）
   * 返回 { ai_enabled: boolean, ai_model: string|null, ai_provider: string|null }
   */
  async getParseConfig() {
    return request('/questions/parse-config')
  },
}

// ——— 报告 ———
export const reports = {
  async getOverview(childId) {
    return request(`/reports/${childId}/overview`)
  },
  async getWrongQuestions(childId) {
    return request(`/reports/${childId}/wrong_questions`)
  },
  async getWeakPoints(childId) {
    return request(`/reports/${childId}/weak_points`)
  },
  async getWeeklyReport(childId) {
    return request(`/reports/${childId}/weekly`)
  },
}
