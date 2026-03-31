import { useEffect, useRef, useState } from 'react'
import { questions as questionsApi } from '../../api.js'
import styles from './QuestionsPage.module.css'

const TAG_LABEL = {
  add_no_carry: '不进位加法', add_with_carry: '进位加法',
  sub_no_borrow: '不退位减法', sub_with_borrow: '退位减法',
  multiply_table: '乘法口诀', unit_conversion: '单位换算',
  mixed_operation: '混合运算', word_problem: '应用题',
}
const TYPE_LABEL = {
  oral_calc: '口算', vertical_calc: '竖式', mixed_calc: '混合运算',
  fill_blank: '填空', unit_convert: '单位换算', word_problem: '应用题',
}

export default function QuestionsPage() {
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [batchText, setBatchText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitMsg, setSubmitMsg] = useState('')
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  // 文件上传相关
  const fileInputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)
  const [parsing, setParsing] = useState(false)
  const [parseMsg, setParseMsg] = useState('')

  // AI 配置状态
  const [aiConfig, setAiConfig] = useState(null)  // { ai_enabled, ai_model, ai_provider }

  const loadQuestions = () => {
    setLoading(true)
    questionsApi.list()
      .then(data => setList(data.questions || data || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadQuestions()
    // 拉取 AI 配置状态
    questionsApi.getParseConfig()
      .then(cfg => setAiConfig(cfg))
      .catch(() => setAiConfig({ ai_enabled: false }))
  }, [])

  // ── 文件上传处理 ──────────────────────────────────────────────
  const handleFile = async (file) => {
    if (!file) return
    const maxSize = 10 * 1024 * 1024  // 10 MB
    if (file.size > maxSize) {
      setParseMsg('❌ 文件太大，请上传 10 MB 以内的文件')
      return
    }
    const allowed = /\.(pdf|jpg|jpeg|png|webp|bmp)$/i
    if (!allowed.test(file.name)) {
      setParseMsg('❌ 不支持的文件格式，请上传 PDF 或图片（JPG / PNG / WEBP）')
      return
    }
    setParsing(true)
    setParseMsg('')
    setSubmitMsg('')
    try {
      const result = await questionsApi.parseFile(file)
      const methodLabel = result.method === 'qwen_vl'
        ? '🤖 通义千问AI'
        : result.method === 'pdf_text' ? 'PDF文字' : 'OCR本地识别'
      setBatchText(result.lines.join('\n'))
      setParseMsg(`✅ ${methodLabel}识别到 ${result.count} 道题，已填入下方，请确认后点击「导入题目」`)
    } catch (err) {
      setParseMsg(`❌ 文件解析失败：${err.message}`)
    } finally {
      setParsing(false)
      // 重置 input，允许重复上传同一文件
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleBatchSubmit = async (e) => {
    e.preventDefault()
    if (!batchText.trim()) return
    const lines = batchText.split('\n').map(l => l.trim()).filter(Boolean)
    if (!lines.length) return
    setSubmitting(true)
    setSubmitMsg('')
    try {
      // ✅ 字段名必须是 original_text（后端 CreateQuestionRequest 的要求）
      const payload = lines.map(text => ({ original_text: text }))
      const result = await questionsApi.batchCreate(payload)
      const count = result.created_count ?? result.length ?? lines.length
      setSubmitMsg(`✅ 成功导入 ${count} 道题目！知识点已自动识别。`)
      setBatchText('')
      loadQuestions()
    } catch (err) {
      setSubmitMsg(`❌ 导入失败：${err.message || '请检查题目格式后重试'}`)
    } finally {
      setSubmitting(false)
    }
  }

  const allTags = ['all', ...Object.keys(TAG_LABEL)]
  const displayed = list.filter(q => {
    const tagOk = filter === 'all' || q.knowledge_tag === filter
    const qText = q.text || q.normalized_text || ''
    const searchOk = !search || qText.includes(search)
    return tagOk && searchOk
  })

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>📚 题库管理</h1>
        <div className={styles.totalBadge}>共 {list.length} 道题</div>
      </div>

      {/* 批量导入 */}
      <div className={`card ${styles.importCard}`}>
        <div className={styles.sectionHeader}>
          <h3 className={styles.sectionTitle}>➕ 批量导入题目</h3>
          {aiConfig && (
            aiConfig.ai_enabled
              ? (
                <span className={styles.aiBadgeOn} title={`模型：${aiConfig.ai_model}`}>
                  🤖 {aiConfig.ai_provider} · 已启用
                </span>
              )
              : (
                <span className={styles.aiBadgeOff} title="配置 DASHSCOPE_API_KEY 后可启用">
                  📦 本地识别（无 AI Key）
                </span>
              )
          )}
        </div>

        {/* AI 未配置时的提示 */}
        {aiConfig && !aiConfig.ai_enabled && (
          <div className={styles.aiHint}>
            💡 使用阿里云通义千问 VL 可大幅提升识别精度。配置方法：
            在后端目录创建 <code>.env</code> 文件，写入{' '}
            <code>DASHSCOPE_API_KEY=你的Key</code>，重启后端即可生效。
            <a
              href="https://dashscope.console.aliyun.com/apiKey"
              target="_blank"
              rel="noreferrer"
              className={styles.aiLink}
            >
              获取免费 API Key →
            </a>
          </div>
        )}

        {/* 文件上传区 */}
        <div
          className={`${styles.dropZone} ${dragOver ? styles.dragOver : ''} ${parsing ? styles.parsingActive : ''}`}
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={e => {
            e.preventDefault()
            setDragOver(false)
            handleFile(e.dataTransfer.files[0])
          }}
          onClick={() => !parsing && fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={e => e.key === 'Enter' && !parsing && fileInputRef.current?.click()}
          aria-label="点击或拖拽上传 PDF 或图片"
        >
          {parsing ? (
            <div className={styles.parsingState}>
              <div className="loading-spinner" style={{ width: 28, height: 28, borderWidth: 3 }} />
              <span>
                {aiConfig?.ai_enabled ? '🤖 通义千问AI 识别中，请稍候…' : '🔍 正在识别文件内容，请稍候…'}
              </span>
            </div>
          ) : (
            <>
              <div className={styles.uploadIcon}>📎</div>
              <div className={styles.uploadText}>
                <strong>点击 或 拖拽文件到此处</strong>
                <span>支持 PDF、JPG、PNG、WEBP（最大 10 MB）</span>
                <span className={styles.uploadNote}>
                  {aiConfig?.ai_enabled
                    ? '✨ 已启用通义千问AI识别 · PDF含文字直接提取 · 扫描件/图片AI理解'
                    : 'PDF 直接提取文字 · 图片/扫描件使用本地OCR（可配置AI提升精度）'}
                </span>
              </div>
            </>
          )}
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.webp,.bmp"
          style={{ display: 'none' }}
          onChange={e => handleFile(e.target.files[0])}
        />
        {parseMsg && (
          <div className={`${styles.parseMsg} ${parseMsg.startsWith('✅') ? styles.parseMsgOk : styles.parseMsgErr}`}>
            {parseMsg}
          </div>
        )}

        {/* 分隔线 */}
        <div className={styles.divider}><span>── 或手动输入题目 ──</span></div>

        <p className={styles.hint}>
          每行一道题，例如：<code>24 + 37 = ___</code>
        </p>
        <form onSubmit={handleBatchSubmit}>
          <textarea
            className={styles.batchInput}
            value={batchText}
            onChange={e => { setBatchText(e.target.value); setSubmitMsg('') }}
            placeholder={"在这里输入题目，每行一道：\n24 + 37 = ___\n63 - 28 = ___\n5 × 6 = ___\n2分米 = ___厘米"}
            rows={6}
          />
          {!batchText.trim() && (
            <p className={styles.inputHint}>👆 请先在上方输入框填写题目，或上传 PDF/图片自动识别</p>
          )}
          {submitMsg && <div className={styles.submitMsg}>{submitMsg}</div>}
          <button
            className="btn btn-primary"
            type="submit"
            disabled={submitting || !batchText.trim()}
            title={!batchText.trim() ? '请先在上方输入框填写题目' : ''}
          >
            {submitting ? '⏳ 导入中…' : '📤 导入题目'}
          </button>
        </form>
      </div>

      {/* 筛选 */}
      <div className={styles.filterRow}>
        <div className={styles.filterTags}>
          {allTags.map(tag => (
            <button
              key={tag}
              className={`${styles.filterBtn} ${filter === tag ? styles.active : ''}`}
              onClick={() => setFilter(tag)}
            >
              {tag === 'all' ? '全部' : TAG_LABEL[tag]}
            </button>
          ))}
        </div>
        <input
          className="input"
          placeholder="搜索题目…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ maxWidth: 200, marginLeft: 'auto' }}
        />
      </div>

      {/* 题目列表 */}
      {loading ? (
        <div className="loading-page"><div className="loading-spinner" /></div>
      ) : displayed.length === 0 ? (
        <div className="empty-state">
          <div className="emoji">🔍</div>
          <p>{list.length === 0 ? '题库为空，快导入一些题目吧！' : '没有符合条件的题目'}</p>
        </div>
      ) : (
        <div className={styles.questionList}>
          {displayed.map((q, i) => (
            <QuestionRow key={q.id || i} q={q} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}

function QuestionRow({ q, index }) {
  return (
    <div className={styles.qRow}>
      <div className={styles.qIndex}>{index + 1}</div>
      <div className={styles.qContent}>
        <div className={styles.qText}>{q.text}</div>
        {q.answer && <div className={styles.qAnswer}>答案：{q.answer}</div>}
      </div>
      <div className={styles.qMeta}>
        {q.question_type && (
          <span className="badge badge-blue" style={{ fontSize: '0.72rem' }}>
            {TYPE_LABEL[q.question_type] || q.question_type}
          </span>
        )}
        {q.knowledge_tag && (
          <span className="badge badge-teal" style={{ fontSize: '0.72rem' }}>
            {TAG_LABEL[q.knowledge_tag] || q.knowledge_tag}
          </span>
        )}
        {q.difficulty && (
          <span className={styles.difficulty}>
            {'⭐'.repeat(q.difficulty)}
          </span>
        )}
      </div>
    </div>
  )
}
