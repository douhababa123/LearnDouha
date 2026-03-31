import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams, useLocation } from 'react-router-dom'
import { missions, questions as questionsApi } from '../../api.js'
import styles from './AnswerPage.module.css'

const TAG_LABEL = {
  add_no_carry: '不进位加法', add_with_carry: '进位加法',
  sub_no_borrow: '不退位减法', sub_with_borrow: '退位减法',
  multiply_table: '乘法口诀', unit_conversion: '单位换算',
  mixed_operation: '混合运算', word_problem: '应用题',
}

export default function AnswerPage() {
  const { childId } = useParams()
  const navigate = useNavigate()
  const { state } = useLocation()
  const inputRef = useRef(null)

  const mission = state?.mission
  const [currentIndex, setCurrentIndex] = useState(state?.currentIndex ?? 0)
  const [answer, setAnswer] = useState('')
  const [attempt, setAttempt] = useState(1)
  const [feedback, setFeedback] = useState(null)   // null | { message, is_correct, ... }
  const [submitting, setSubmitting] = useState(false)
  const [similarQuestions, setSimilarQuestions] = useState([])
  const [showSimilar, setShowSimilar] = useState(false)
  const [answered, setAnswered] = useState(false)

  // 当前题目
  const allQ = mission?.questions || []
  // 找第一道未答对的
  const pendingIndices = allQ
    .map((q, i) => ({ q, i }))
    .filter(({ q }) => !q.is_correct)
  const currentEntry = allQ[currentIndex]

  useEffect(() => {
    setAnswer('')
    setAttempt(1)
    setFeedback(null)
    setSimilarQuestions([])
    setShowSimilar(false)
    setAnswered(false)
    setTimeout(() => inputRef.current?.focus(), 100)
  }, [currentIndex])

  if (!mission) {
    return (
      <div className={styles.page}>
        <div className="empty-state">
          <div className="emoji">😅</div>
          <p>没有找到任务数据，请返回重试</p>
          <br />
          <button className="btn btn-primary" onClick={() => navigate(`/child/${childId}/home`)}>返回</button>
        </div>
      </div>
    )
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!answer.trim() || submitting) return
    setSubmitting(true)
    try {
      const res = await missions.submitAnswer(
        currentEntry.mission_question_id,
        answer.trim(),
        attempt
      )
      setFeedback(res)
      setAnswered(res.is_correct || res.feedback.show_answer)

      if (!res.is_correct && res.feedback.show_explanation) {
        // 触发类似题
        const similar = await questionsApi.getSimilar(currentEntry.question_id).catch(() => null)
        if (similar?.similar_questions?.length > 0) {
          setSimilarQuestions(similar.similar_questions)
        }
      }
    } catch (err) {
      setFeedback({ error: err.message })
    } finally {
      setSubmitting(false)
    }
  }

  function handleRetry() {
    setAnswer('')
    setAttempt(a => a + 1)
    setFeedback(null)
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  function handleNext() {
    // 找下一道未答对的题
    const nextPending = allQ.findIndex((q, i) => i > currentIndex && !q.is_correct && !q.is_answered)
    if (nextPending !== -1) {
      setCurrentIndex(nextPending)
    } else {
      navigate(`/child/${childId}/result`, { state: { mission } })
    }
  }

  const q = currentEntry
  if (!q) return null
  const answered_ok = feedback?.is_correct
  const show_answer = feedback?.feedback?.show_answer
  const can_retry = feedback?.feedback?.can_retry

  const progressNum = allQ.filter(q => q.is_correct || q.is_answered).length
  const progressPct = Math.round(progressNum / allQ.length * 100)

  return (
    <div className={styles.page}>
      {/* 顶部进度 */}
      <div className={styles.topbar}>
        <button className={styles.back} onClick={() => navigate(`/child/${childId}/mission`)}>←</button>
        <div className={styles.topCenter}>
          <div className={styles.qCounter}>{currentIndex + 1} / {allQ.length}</div>
          <div className="progress-bar" style={{ flex: 1 }}>
            <div className="progress-fill" style={{ width: `${progressPct}%` }} />
          </div>
        </div>
        <div className={styles.topRight}>
          <span className="badge badge-purple">{TAG_LABEL[q.knowledge_tag] || ''}</span>
        </div>
      </div>

      <div className={styles.content}>
        {/* 题目区 */}
        <div className={`${styles.questionBox} ${feedback ? (answered_ok ? styles.questionCorrect : styles.questionWrong) : ''}`}>
          <div className={styles.questionLabel}>题目</div>
          <div className={styles.questionText}>{q.text}</div>
        </div>

        {/* 反馈区 */}
        {feedback && (
          <div className={`${styles.feedbackBox} ${answered_ok ? styles.feedbackCorrect : styles.feedbackWrong} anim-pop`}>
            <div className={styles.feedbackIcon}>{answered_ok ? '🎉' : (can_retry ? '💪' : '📖')}</div>
            <div className={styles.feedbackMsg}>{feedback.feedback?.message || feedback.error}</div>
            {feedback.feedback?.hint && (
              <div className={styles.hint}>💡 {feedback.feedback.hint}</div>
            )}
            {show_answer && feedback.correct_answer && (
              <div className={styles.correctAnswer}>
                正确答案是：<strong>{feedback.correct_answer}</strong>
              </div>
            )}
          </div>
        )}

        {/* 类似题强化 */}
        {showSimilar && similarQuestions.length > 0 && (
          <div className={`${styles.similarBox} anim-fade`}>
            <div className={styles.similarTitle}>💪 强化练习（同知识点）</div>
            {similarQuestions.map((sq, i) => (
              <div key={sq.question_id} className={styles.similarItem}>
                <span className={styles.similarNum}>{i + 1}</span>
                <span>{sq.text}</span>
              </div>
            ))}
          </div>
        )}

        {/* 输入区 */}
        {!answered_ok && !show_answer && (
          <form onSubmit={handleSubmit} className={styles.answerForm}>
            <input
              ref={inputRef}
              className={`input input-answer ${styles.answerInput} ${feedback && !answered_ok ? 'anim-shake' : ''}`}
              type="text"
              inputMode="numeric"
              placeholder="写出你的答案"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              disabled={submitting}
              autoComplete="off"
            />
            <button
              className={`btn btn-primary btn-block btn-lg ${styles.submitBtn}`}
              type="submit"
              disabled={!answer.trim() || submitting}
            >
              {submitting ? '判断中…' : '✓ 提交答案'}
            </button>
          </form>
        )}

        {/* 操作按钮区 */}
        {feedback && (
          <div className={styles.actionArea}>
            {can_retry && !answered_ok && (
              <button className="btn btn-teal btn-block btn-lg" onClick={handleRetry}>
                🔄 再试一次
              </button>
            )}
            {similarQuestions.length > 0 && !showSimilar && (
              <button className="btn btn-yellow btn-block" onClick={() => setShowSimilar(true)}>
                💡 看强化练习
              </button>
            )}
            {(answered_ok || show_answer) && (
              <button className="btn btn-primary btn-block btn-lg" onClick={handleNext}>
                下一题 →
              </button>
            )}
          </div>
        )}

        {/* 尝试次数指示 */}
        {attempt > 1 && !feedback && (
          <div className={styles.attemptHint}>第 {attempt} 次尝试</div>
        )}
      </div>
    </div>
  )
}
