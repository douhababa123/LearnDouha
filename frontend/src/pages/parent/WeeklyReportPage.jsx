import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { reports } from '../../api.js'
import styles from './WeeklyReportPage.module.css'

const TAG_LABEL = {
  add_no_carry: '不进位加法', add_with_carry: '进位加法',
  sub_no_borrow: '不退位减法', sub_with_borrow: '退位减法',
  multiply_table: '乘法口诀', unit_conversion: '单位换算',
  mixed_operation: '混合运算', word_problem: '应用题',
}

export default function WeeklyReportPage() {
  const { childId } = useOutletContext()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!childId) return
    setLoading(true)
    reports.getWeeklyReport(childId)
      .then(setReport)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [childId])

  if (!childId) return <div className="empty-state"><div className="emoji">👈</div><p>请先选择孩子</p></div>
  if (loading)  return <div className="loading-page"><div className="loading-spinner" /></div>
  if (!report)  return <div className="empty-state"><div className="emoji">📊</div><p>暂无报告数据</p></div>

  const accuracy = Math.round((report.avg_accuracy || 0) * 100)

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>📈 本周学习报告</h1>
        <div className={styles.weekRange}>{report.week_start} ~ {report.week_end}</div>
      </div>

      {/* AI 总结 */}
      {report.ai_summary && (
        <div className={styles.aiCard}>
          <div className={styles.aiHeader}>
            <span className={styles.aiIcon}>🤖</span>
            <span>AI 学习总结</span>
          </div>
          <p className={styles.aiText}>{report.ai_summary}</p>
        </div>
      )}

      {/* 核心数据 */}
      <div className={styles.metricsGrid}>
        <MetricBox icon="📅" value={`${report.completion_days}/7`} label="完成天数"
          sub={report.completion_days >= 5 ? '非常好！' : '加油！'} color="#4ECDC4" />
        <MetricBox icon="🎯" value={`${accuracy}%`} label="平均正确率"
          sub={accuracy >= 80 ? '优秀' : accuracy >= 60 ? '良好' : '需加强'} color={accuracy >= 80 ? '#6BCB77' : '#F6AD55'} />
        <MetricBox icon="📝" value={report.total_questions} label="完成题数"
          sub="本周累计" color="#FF6B6B" />
      </div>

      {/* 薄弱点 */}
      {report.weak_points?.length > 0 && (
        <div className={`card ${styles.section}`}>
          <h3 className={styles.sectionTitle}>⚠️ 需要加强</h3>
          <div className={styles.tagList}>
            {report.weak_points.map(wp => (
              <div key={wp.knowledge_tag} className={styles.weakTag}>
                <span>📌 {TAG_LABEL[wp.knowledge_tag] || wp.knowledge_tag}</span>
                <span className="badge badge-red">{Math.round(wp.error_rate * 100)}% 错误率</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 进步点 */}
      {report.progress_points?.length > 0 && (
        <div className={`card ${styles.section}`}>
          <h3 className={styles.sectionTitle}>🚀 进步最大</h3>
          <div className={styles.tagList}>
            {report.progress_points.map(pp => (
              <div key={pp.knowledge_tag} className={styles.progressTag}>
                <span>✅ {TAG_LABEL[pp.knowledge_tag] || pp.knowledge_tag}</span>
                <span className="badge badge-green">{Math.round(pp.accuracy * 100)}% 正确率</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 明日推荐 */}
      {report.weak_points?.length > 0 && (
        <div className={styles.recommendCard}>
          <div className={styles.recommendTitle}>🔮 明日重点推荐练习</div>
          <div className={styles.recommendTags}>
            {report.weak_points.slice(0, 2).map(wp => (
              <span key={wp.knowledge_tag} className={styles.recommendTag}>
                {TAG_LABEL[wp.knowledge_tag] || wp.knowledge_tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function MetricBox({ icon, value, label, sub, color }) {
  return (
    <div className={styles.metricBox}>
      <div className={styles.metricIcon}>{icon}</div>
      <div className={styles.metricValue} style={{ color }}>{value}</div>
      <div className={styles.metricLabel}>{label}</div>
      <div className={styles.metricSub}>{sub}</div>
    </div>
  )
}
