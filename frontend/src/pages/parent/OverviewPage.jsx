import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { reports } from '../../api.js'
import styles from './OverviewPage.module.css'

export default function OverviewPage() {
  const { childId, selectedChild } = useOutletContext()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!childId) return
    setLoading(true)
    reports.getOverview(childId)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [childId])

  if (!childId) return (
    <div className="empty-state">
      <div className="emoji">👈</div>
      <p>请先在左侧添加孩子</p>
    </div>
  )

  if (loading) return <div className="loading-page"><div className="loading-spinner" /></div>
  if (!data) return <div className="empty-state"><div className="emoji">😅</div><p>暂无数据</p></div>

  const accuracy = Math.round((data.accuracy_rate || 0) * 100)
  const completePct = data.total_questions > 0
    ? Math.round(data.completed_questions / data.total_questions * 100) : 0

  return (
    <div className={styles.page}>
      <div className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>📊 今日学习总览</h1>
          <p className={styles.pageDate}>{new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
        <div className={`${styles.completeBadge} ${data.is_completed ? styles.completeBadgeDone : ''}`}>
          {data.is_completed ? '✅ 已完成' : '⏳ 进行中'}
        </div>
      </div>

      {/* 核心指标 */}
      <div className={styles.metricsGrid}>
        <MetricCard icon="✅" value={data.is_completed ? '是' : '否'} label="今日是否完成"
          color={data.is_completed ? '#6BCB77' : '#F6AD55'} />
        <MetricCard icon="🎯" value={`${accuracy}%`} label="今日正确率"
          color={accuracy >= 80 ? '#6BCB77' : accuracy >= 60 ? '#F6AD55' : '#FC8181'} />
        <MetricCard icon="🔥" value={`${data.current_streak} 天`} label="连续打卡" color="#FF6B6B" />
        <MetricCard icon="📝" value={`${data.completed_questions}/${data.total_questions}`} label="完成题量" color="#4ECDC4" />
      </div>

      {/* 今日进度条 */}
      {data.total_questions > 0 && (
        <div className={`card ${styles.progressCard}`}>
          <div className={styles.progressHeader}>
            <span className={styles.progressLabel}>今日进度</span>
            <span className={styles.progressValue}>{completePct}%</span>
          </div>
          <div className="progress-bar" style={{ height: '16px' }}>
            <div className="progress-fill" style={{ width: `${completePct}%` }} />
          </div>
          <div className={styles.progressNote}>
            已完成 {data.completed_questions} 题，共 {data.total_questions} 题
          </div>
        </div>
      )}

      {/* 打卡记录 */}
      <div className={`card ${styles.streakCard}`}>
        <h3 className={styles.cardTitle}>🔥 打卡记录</h3>
        <div className={styles.streakRow}>
          <StreakItem icon="🔥" value={data.current_streak} label="当前连续" />
          <StreakItem icon="📅" value={data.total_checkins} label="累计打卡" />
        </div>
        {/* 模拟本周打卡日历 */}
        <div className={styles.weekCalendar}>
          {['一', '二', '三', '四', '五', '六', '日'].map((day, i) => {
            const today = new Date().getDay()
            const dayOfWeek = today === 0 ? 6 : today - 1  // 0=周一
            const isTodayOrPast = i <= dayOfWeek
            const isToday = i === dayOfWeek
            return (
              <div key={day} className={`${styles.calDay} ${isTodayOrPast && data.current_streak > 0 ? styles.calDayDone : ''} ${isToday ? styles.calDayToday : ''}`}>
                <div className={styles.calDayNum}>{day}</div>
                <div className={styles.calDayIcon}>{isTodayOrPast && data.current_streak > 0 ? '⭐' : '○'}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function MetricCard({ icon, value, label, color }) {
  return (
    <div className={styles.metricCard}>
      <div className={styles.metricIcon}>{icon}</div>
      <div className={styles.metricValue} style={{ color }}>{value}</div>
      <div className={styles.metricLabel}>{label}</div>
    </div>
  )
}

function StreakItem({ icon, value, label }) {
  return (
    <div className={styles.streakItem}>
      <div className={styles.streakIcon}>{icon}</div>
      <div className={styles.streakVal}>{value}</div>
      <div className={styles.streakLabel}>{label}</div>
    </div>
  )
}
