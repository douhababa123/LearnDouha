import { useState, useEffect } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { children as childrenApi, auth } from '../../api.js'
import styles from './ParentLayout.module.css'

export default function ParentLayout() {
  const navigate = useNavigate()
  const [children, setChildren] = useState([])
  const [selectedChild, setSelectedChild] = useState(null)
  const [showAddChild, setShowAddChild] = useState(false)
  const [newNickname, setNewNickname] = useState('')
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    childrenApi.list().then(list => {
      setChildren(list)
      if (list.length > 0) setSelectedChild(list[0])
    }).catch(console.error)
  }, [])

  async function handleAddChild(e) {
    e.preventDefault()
    if (!newNickname.trim()) return
    setAdding(true)
    try {
      const child = await childrenApi.create(newNickname.trim())
      const updated = await childrenApi.list()
      setChildren(updated)
      setSelectedChild(updated.find(c => c.child_id === child.child_id) || updated[0])
      setShowAddChild(false)
      setNewNickname('')
    } catch (e) {
      alert(e.message)
    } finally {
      setAdding(false)
    }
  }

  const childId = selectedChild?.child_id

  return (
    <div className={styles.layout}>
      {/* 侧边栏 */}
      <aside className={styles.sidebar}>
        <div className={styles.sideHeader}>
          <div className={styles.logo}>🏝️</div>
          <div>
            <div className={styles.logoTitle}>数学冒险岛</div>
            <div className={styles.logoSub}>家长后台</div>
          </div>
        </div>

        {/* 孩子选择 */}
        <div className={styles.childSection}>
          <div className={styles.childLabel}>当前孩子</div>
          {children.length === 0 ? (
            <div className={styles.noChild}>还没有孩子，请添加</div>
          ) : (
            <div className={styles.childList}>
              {children.map(c => (
                <button key={c.child_id}
                  className={`${styles.childBtn} ${selectedChild?.child_id === c.child_id ? styles.childBtnActive : ''}`}
                  onClick={() => setSelectedChild(c)}>
                  🐿️ {c.nickname}
                </button>
              ))}
            </div>
          )}
          <button className={`btn btn-sm btn-teal ${styles.addChildBtn}`}
            onClick={() => setShowAddChild(v => !v)}>
            + 添加孩子
          </button>
          {showAddChild && (
            <form onSubmit={handleAddChild} className={styles.addChildForm}>
              <input className="input" placeholder="孩子昵称"
                value={newNickname} onChange={e => setNewNickname(e.target.value)} />
              <button className="btn btn-primary btn-sm btn-block" type="submit" disabled={adding}>
                {adding ? '添加中…' : '确认添加'}
              </button>
            </form>
          )}
        </div>

        {/* 导航 */}
        <nav className={styles.nav}>
          {[
            { to: '/parent/overview', icon: '📊', label: '今日总览' },
            { to: '/parent/wrong-questions', icon: '❌', label: '错题记录' },
            { to: '/parent/weekly', icon: '📈', label: '周报告' },
            { to: '/parent/questions', icon: '📝', label: '题目管理' },
          ].map(item => (
            <NavLink key={item.to} to={item.to}
              className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}>
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* 切换孩子端 */}
        {childId && (
          <button className={`btn btn-yellow btn-sm ${styles.switchBtn}`}
            onClick={() => navigate(`/child/${childId}/home`)}>
            👦 切换到孩子视角
          </button>
        )}

        <button className={`btn btn-outline btn-sm ${styles.logoutBtn}`}
          onClick={() => { auth.logout(); navigate('/login') }}>
          退出登录
        </button>
      </aside>

      {/* 主内容 */}
      <main className={styles.main}>
        {/* 传递 childId 给子页面 */}
        <Outlet context={{ childId, selectedChild }} />
      </main>
    </div>
  )
}
