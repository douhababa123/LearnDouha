import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { missions, children as childrenApi, auth } from '../../api.js'
import styles from './ChildHome.module.css'

// 剧情章节数据（第一条主线：小松鼠的冬日准备）
const CHAPTERS = [
  { id: 1, title: '收集松果',   icon: '🌰', desc: '帮小松鼠收集过冬的松果' },
  { id: 2, title: '整理树洞',   icon: '🕳️', desc: '把树洞整理得干干净净' },
  { id: 3, title: '修补小桥',   icon: '🌉', desc: '修好通往森林的小桥' },
  { id: 4, title: '寻找朋友',   icon: '🦔', desc: '去找小刺猬一起准备' },
  { id: 5, title: '准备食物',   icon: '🍎', desc: '储存好冬天的食物' },
  { id: 6, title: '躲避风雪',   icon: '❄️', desc: '安全躲过大风雪' },
  { id: 7, title: '完成过冬准备', icon: '🏠', desc: '温暖过冬！' },
]

export default function ChildHome() {
  const { childId } = useParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState(null)
  const [streak, setStreak] = useState(null)
  const [loading, setLoading] = useState(true)
  const [currentChapter] = useState(1)  // 实际应从后端获取进度

  useEffect(() => {
    Promise.all([
      missions.getTodayStatus(childId),
      childrenApi.getStreak(childId),
    ]).then(([s, st]) => {
      setStatus(s)
      setStreak(st)
    }).catch(console.error)
      .finally(() => setLoading(false))
  }, [childId])

  async function handleStartMission() {
    navigate(`/child/${childId}/mission`)
  }

  if (loading) {
    return (
      <div className={styles.page}>
        <div className="loading-page">
          <div className="loading-spinner" />
          <span>加载中…</span>
        </div>
      </div>
    )
  }

  const progress = status?.total_questions > 0
    ? Math.round(status.completed_questions / status.total_questions * 100)
    : 0

  const chapter = CHAPTERS[currentChapter - 1]

  return (
    <div className={styles.page}>
      {/* 顶部：孩子信息 */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.avatar}>🐿️</div>
          <div>
            <div className={styles.greeting}>你好，小冒险家！</div>
            <div className={styles.date}>{new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })}</div>
          </div>
        </div>
        <div className={styles.streakBadge}>
          🔥 {streak?.current_streak || 0} 天
        </div>
      </header>

      {/* 剧情卡片 */}
      <div className={styles.storyCard}>
        <div className={styles.storyLabel}>📖 今日冒险任务</div>
        <div className={styles.storyChapter}>
          <span className={styles.chapterIcon}>{chapter.icon}</span>
          <div>
            <div className={styles.chapterTitle}>第{currentChapter}关：{chapter.title}</div>
            <div className={styles.chapterDesc}>{chapter.desc}</div>
          </div>
        </div>

        {/* 关卡进度地图 */}
        <div className={styles.chapterMap}>
          {CHAPTERS.map((c, i) => (
            <div
              key={c.id}
              className={`${styles.mapNode} ${i < currentChapter ? styles.mapNodeDone : ''} ${i === currentChapter - 1 ? styles.mapNodeCurrent : ''}`}
            >
              <span>{i < currentChapter - 1 ? '✅' : c.icon}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 今日任务状态 */}
      <div className={styles.missionCard}>
        <div className={styles.missionHeader}>
          <span className={styles.missionTitle}>📚 今日练习</span>
          {status?.is_completed && (
            <span className="badge badge-green">✅ 已完成</span>
          )}
        </div>

        {status?.has_mission ? (
          <>
            <div className={styles.missionStats}>
              <div className={styles.stat}>
                <div className={styles.statNum}>{status.completed_questions}</div>
                <div className={styles.statLabel}>已完成</div>
              </div>
              <div className={styles.statDivider} />
              <div className={styles.stat}>
                <div className={styles.statNum}>{status.total_questions}</div>
                <div className={styles.statLabel}>共计</div>
              </div>
              <div className={styles.statDivider} />
              <div className={styles.stat}>
                <div className={styles.statNum}>{Math.round((status.accuracy_rate || 0) * 100)}%</div>
                <div className={styles.statLabel}>正确率</div>
              </div>
            </div>
            <div className="progress-bar" style={{ margin: '16px 0 20px' }}>
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </>
        ) : (
          <div className={styles.noMission}>今天的任务还没开始，点击下面开始吧！</div>
        )}

        <button
          className={`btn btn-lg btn-block ${status?.is_completed ? 'btn-outline' : 'btn-primary'}`}
          onClick={handleStartMission}
        >
          {status?.is_completed ? '🎉 再做一遍' : status?.has_mission ? '▶️ 继续答题' : '🚀 开始今日冒险'}
        </button>
      </div>

      {/* 成就栏 */}
      <div className={styles.achievements}>
        <div className={styles.achievement}>
          <div className={styles.achieveIcon}>🔥</div>
          <div className={styles.achieveVal}>{streak?.current_streak || 0}</div>
          <div className={styles.achieveLabel}>连续天数</div>
        </div>
        <div className={styles.achievement}>
          <div className={styles.achieveIcon}>⭐</div>
          <div className={styles.achieveVal}>{streak?.total_checkins || 0}</div>
          <div className={styles.achieveLabel}>累计打卡</div>
        </div>
        <div className={styles.achievement}>
          <div className={styles.achieveIcon}>🏆</div>
          <div className={styles.achieveVal}>{streak?.max_streak || 0}</div>
          <div className={styles.achieveLabel}>最长连续</div>
        </div>
      </div>

      {/* 退出按钮 */}
      <button className={`btn btn-outline btn-sm ${styles.logoutBtn}`} onClick={() => {
        auth.logout(); navigate('/login')
      }}>退出</button>
    </div>
  )
}
