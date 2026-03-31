import { useNavigate, useParams, useLocation } from 'react-router-dom'
import styles from './ResultPage.module.css'

const STARS = ['⭐', '🌟', '💫']

export default function ResultPage() {
  const { childId } = useParams()
  const navigate = useNavigate()
  const { state } = useLocation()
  const mission = state?.mission

  if (!mission) {
    navigate(`/child/${childId}/home`)
    return null
  }

  const total = mission.questions.length
  const correct = mission.questions.filter(q => q.is_correct).length
  const rate = total > 0 ? Math.round(correct / total * 100) : 0
  const stars = rate >= 90 ? 3 : rate >= 70 ? 2 : 1

  return (
    <div className={styles.page}>
      {/* 背景星星 */}
      <div className={styles.starsBg}>
        {Array.from({ length: 20 }).map((_, i) => (
          <span key={i} className={styles.starParticle}
            style={{ left: `${Math.random() * 100}%`, animationDelay: `${Math.random() * 3}s`, fontSize: `${16 + Math.random() * 24}px` }}>
            {['⭐', '🌟', '💫', '✨'][Math.floor(Math.random() * 4)]}
          </span>
        ))}
      </div>

      <div className={styles.content}>
        {/* 主角庆祝 */}
        <div className={`${styles.hero} anim-bounce`}>🐿️</div>
        <div className={`${styles.title} anim-pop`}>
          {rate >= 90 ? '完美！超级棒！' : rate >= 70 ? '做得很好！' : '继续加油！'}
        </div>

        {/* 星星评分 */}
        <div className={`${styles.stars} anim-pop`}>
          {Array.from({ length: 3 }).map((_, i) => (
            <span key={i} className={`${styles.star} ${i < stars ? styles.starOn : styles.starOff}`}
              style={{ animationDelay: `${i * 0.15}s` }}>⭐</span>
          ))}
        </div>

        {/* 数据卡 */}
        <div className={`${styles.statsCard} anim-fade`}>
          <div className={styles.statsRow}>
            <div className={styles.statItem}>
              <div className={styles.statNum} style={{ color: '#FF6B6B' }}>{correct}</div>
              <div className={styles.statLabel}>答对</div>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.statItem}>
              <div className={styles.statNum} style={{ color: '#4ECDC4' }}>{total - correct}</div>
              <div className={styles.statLabel}>错误</div>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.statItem}>
              <div className={styles.statNum} style={{ color: '#FFE66D', WebkitTextStroke: '1px #F5C800' }}>{rate}%</div>
              <div className={styles.statLabel}>正确率</div>
            </div>
          </div>
        </div>

        {/* 剧情推进 */}
        <div className={`${styles.storyAdvance} anim-fade`}>
          <div className={styles.storyIcon}>🌰</div>
          <div>
            <div className={styles.storyTitle}>剧情推进：收集松果</div>
            <div className={styles.storyText}>
              {rate >= 90
                ? '你帮小松鼠收集到了满满一篮松果！它开心地蹦蹦跳跳～'
                : rate >= 70
                ? '小松鼠收集到了不少松果，明天继续努力！'
                : '小松鼠还需要你的帮助，明天一起加油吧！'}
            </div>
          </div>
        </div>

        {/* 明日预告 */}
        <div className={styles.nextPreview}>
          <span>🔮 明日任务预告：</span>
          <strong>整理树洞 🕳️</strong>
        </div>

        {/* 按钮 */}
        <div className={styles.actions}>
          <button className="btn btn-primary btn-block btn-lg"
            onClick={() => navigate(`/child/${childId}/home`)}>
            🏠 返回主页
          </button>
          <button className="btn btn-outline btn-block"
            onClick={() => navigate(`/child/${childId}/mission`, { state: { mission } })}>
            📋 查看错题
          </button>
        </div>
      </div>
    </div>
  )
}
