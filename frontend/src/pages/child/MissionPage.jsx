import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { missions } from '../../api.js'
import styles from './MissionPage.module.css'

const TYPE_LABEL = {
  oral_calc: '口算',
  vertical_calc: '竖式',
  mixed_calc: '脱式',
  fill_blank: '填空',
  unit_convert: '单位',
  word_problem: '应用题',
}

const TAG_LABEL = {
  add_no_carry: '不进位加法',
  add_with_carry: '进位加法',
  sub_no_borrow: '不退位减法',
  sub_with_borrow: '退位减法',
  multiply_table: '乘法口诀',
  unit_conversion: '单位换算',
  mixed_operation: '混合运算',
  word_problem: '应用题',
}

export default function MissionPage() {
  const { childId } = useParams()
  const navigate = useNavigate()
  const [mission, setMission] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    missions.getOrCreate(childId)
      .then(setMission)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [childId])

  if (loading) return (
    <div className={styles.page}>
      <div className="loading-page">
        <div className="loading-spinner" />
        <span>正在生成今日任务…</span>
      </div>
    </div>
  )

  if (error) {
    const isEmpty = error.includes('题目池为空') || error.includes('题库')
    return (
      <div className={styles.page}>
        <div className={styles.topbar}>
          <button className="topbar-back" onClick={() => navigate(`/child/${childId}/home`)}>←</button>
          <span className="topbar-title">今日任务</span>
          <span />
        </div>
        {isEmpty ? (
          <div className={styles.emptyGuide}>
            <div className={styles.emptyIcon}>📚</div>
            <h3 className={styles.emptyTitle}>还没有练习题哦！</h3>
            <p className={styles.emptyDesc}>需要爸爸妈妈先去添加题目，才能开始冒险～</p>
            <div className={styles.steps}>
              <div className={styles.step}><span className={styles.stepNum}>1</span><span>家长登录后点击右上角「家长端」</span></div>
              <div className={styles.step}><span className={styles.stepNum}>2</span><span>点击左侧菜单「📚 题库管理」</span></div>
              <div className={styles.step}><span className={styles.stepNum}>3</span><span>在输入框里输入题目（每行一道）</span></div>
              <div className={styles.step}><span className={styles.stepNum}>4</span><span>点击「📤 导入题目」按钮</span></div>
              <div className={styles.step}><span className={styles.stepNum}>5</span><span>回来重新点击「开始今日冒险」🚀</span></div>
            </div>
            <div className={styles.exampleBox}>
              <div className={styles.exampleTitle}>题目格式示例：</div>
              <code className={styles.exampleCode}>
                {`23 + 45 = ___\n67 - 28 = ___\n6 × 7 = ___\n2米 = ___厘米`}
              </code>
            </div>
            <button className="btn btn-primary" onClick={() => navigate(`/child/${childId}/home`)}>
              ← 返回主页
            </button>
          </div>
        ) : (
          <div className="empty-state">
            <div className="emoji">😅</div>
            <p>{error}</p>
            <br />
            <button className="btn btn-primary" onClick={() => navigate(`/child/${childId}/home`)}>返回主页</button>
          </div>
        )}
      </div>
    )
  }

  const answered = mission.questions.filter(q => q.is_answered).length
  const total = mission.questions.length
  const progress = total > 0 ? Math.round(answered / total * 100) : 0

  return (
    <div className={styles.page}>
      {/* 顶部 */}
      <div className={styles.topbar}>
        <button className={styles.back} onClick={() => navigate(`/child/${childId}/home`)}>←</button>
        <div className={styles.topCenter}>
          <div className={styles.topTitle}>今日任务</div>
          <div className={styles.topProgress}>{answered}/{total} 已完成</div>
        </div>
        <div className={styles.topPercent}>{progress}%</div>
      </div>

      {/* 进度条 */}
      <div className={styles.progressWrap}>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* 题目列表 */}
      <div className={styles.questionList}>
        {mission.questions.map((q, idx) => (
          <button
            key={q.mission_question_id}
            className={`${styles.questionItem} ${q.is_answered ? (q.is_correct ? styles.correct : styles.wrong) : ''}`}
            onClick={() => navigate(`/child/${childId}/answer`, {
              state: { mission, currentIndex: idx }
            })}
            disabled={q.is_answered && q.is_correct}
          >
            <div className={styles.qLeft}>
              <span className={styles.qNum}>{idx + 1}</span>
              <div>
                <div className={styles.qText}>{q.text}</div>
                <div className={styles.qTags}>
                  <span className={`badge badge-blue`}>{TYPE_LABEL[q.question_type] || q.question_type}</span>
                  <span className={`badge badge-purple`}>{TAG_LABEL[q.knowledge_tag] || q.knowledge_tag}</span>
                  {q.category === 'wrong_recycle' && <span className="badge badge-red">错题</span>}
                </div>
              </div>
            </div>
            <div className={styles.qStatus}>
              {q.is_answered
                ? (q.is_correct ? '✅' : '❌')
                : '▶️'}
            </div>
          </button>
        ))}
      </div>

      {/* 全部完成提示 */}
      {mission.is_completed && (
        <div className={styles.completeBanner}>
          <div className={styles.completeBannerContent}>
            <div>🎉 今天全部完成了！太棒了！</div>
            <button className="btn btn-yellow btn-sm"
              onClick={() => navigate(`/child/${childId}/result`, { state: { mission } })}>
              查看结算
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
