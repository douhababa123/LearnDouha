import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { reports } from '../../api.js'
import styles from './WrongQuestionsPage.module.css'

const TAG_LABEL = {
  add_no_carry: '不进位加法', add_with_carry: '进位加法',
  sub_no_borrow: '不退位减法', sub_with_borrow: '退位减法',
  multiply_table: '乘法口诀', unit_conversion: '单位换算',
  mixed_operation: '混合运算', word_problem: '应用题',
}

export default function WrongQuestionsPage() {
  const { childId } = useOutletContext()
  const [wrongList, setWrongList] = useState([])
  const [weakPoints, setWeakPoints] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!childId) return
    setLoading(true)
    Promise.all([
      reports.getWrongQuestions(childId),
      reports.getWeakPoints(childId),
    ]).then(([wq, wp]) => {
      setWrongList(wq)
      setWeakPoints(wp.weak_points || [])
    }).catch(console.error)
      .finally(() => setLoading(false))
  }, [childId])

  if (!childId) return <div className="empty-state"><div className="emoji">👈</div><p>请先选择孩子</p></div>
  if (loading)  return <div className="loading-page"><div className="loading-spinner" /></div>

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>❌ 错题 & 薄弱点分析</h1>

      {/* 薄弱点 */}
      <div className={`card ${styles.weakCard}`}>
        <h3 className={styles.sectionTitle}>⚠️ 薄弱知识点（近7天）</h3>
        {weakPoints.length === 0 ? (
          <div className={styles.allGood}>🎉 暂无明显薄弱点，继续保持！</div>
        ) : (
          <div className={styles.weakList}>
            {weakPoints.map((wp, i) => (
              <div key={wp.knowledge_tag} className={styles.weakItem}>
                <div className={styles.weakRank}>{i + 1}</div>
                <div className={styles.weakInfo}>
                  <div className={styles.weakTag}>{TAG_LABEL[wp.knowledge_tag] || wp.knowledge_tag}</div>
                  <div className={styles.weakStats}>
                    错误率 {Math.round(wp.error_rate * 100)}% · 共 {wp.total} 题
                  </div>
                </div>
                <div className={styles.weakBar}>
                  <div className={styles.weakBarFill} style={{ width: `${Math.round(wp.error_rate * 100)}%` }} />
                </div>
                <span className={`badge ${wp.error_rate > 0.6 ? 'badge-red' : wp.error_rate > 0.4 ? 'badge-yellow' : 'badge-blue'}`}>
                  {Math.round(wp.error_rate * 100)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 错题列表 */}
      <div className={`card ${styles.wrongCard}`}>
        <h3 className={styles.sectionTitle}>📋 错题记录 ({wrongList.length})</h3>
        {wrongList.length === 0 ? (
          <div className={styles.allGood}>🎉 还没有错题记录！</div>
        ) : (
          <div className={styles.wrongList}>
            {wrongList.map(item => (
              <div key={item.question_id} className={styles.wrongItem}>
                <div className={styles.wrongLeft}>
                  <div className={styles.wrongText}>{item.text}</div>
                  <div className={styles.wrongMeta}>
                    <span className="badge badge-purple">{TAG_LABEL[item.knowledge_tag] || item.knowledge_tag}</span>
                    <span className={`badge ${item.is_mastered ? 'badge-green' : 'badge-red'}`}>
                      {item.is_mastered ? '已掌握' : `错 ${item.wrong_count} 次`}
                    </span>
                    {item.is_reinforced && <span className="badge badge-blue">已强化</span>}
                  </div>
                </div>
                <div className={styles.wrongDate}>{new Date(item.last_wrong_at).toLocaleDateString('zh-CN')}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
