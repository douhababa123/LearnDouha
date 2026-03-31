import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { auth, children as childrenApi } from '../api.js'
import styles from './Login.module.css'

export default function Login() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [role, setRole] = useState('parent')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [nickname, setNickname] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleLogin(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await auth.login(username, password)
      localStorage.setItem('token', res.access_token)
      localStorage.setItem('role', res.role)
      localStorage.setItem('userId', res.user_id)

      if (res.role === 'parent') {
        navigate('/parent/overview')
      } else {
        // 孩子登录后跳转（示例用child_id=1）
        navigate(`/child/${res.user_id}/home`)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleRegister(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await auth.register(username, password, role, nickname || username)
      // 注册后直接登录
      const res = await auth.login(username, password)
      localStorage.setItem('token', res.access_token)
      localStorage.setItem('role', res.role)
      localStorage.setItem('userId', res.user_id)
      navigate('/parent/overview')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      {/* 背景装饰 */}
      <div className={styles.bgDecor}>
        <span>🌟</span><span>🦔</span><span>🍀</span>
        <span>🌈</span><span>🎯</span><span>⭐</span>
      </div>

      <div className={styles.card}>
        {/* Logo区 */}
        <div className={styles.logo}>
          <div className={styles.logoIcon}>🏝️</div>
          <h1 className={styles.logoTitle}>数学冒险岛</h1>
          <p className={styles.logoSub}>和小松鼠一起冒险学数学！</p>
        </div>

        {/* Tab切换 */}
        <div className={styles.tabs}>
          <button
            className={`${styles.tab} ${mode === 'login' ? styles.tabActive : ''}`}
            onClick={() => { setMode('login'); setError('') }}
          >登录</button>
          <button
            className={`${styles.tab} ${mode === 'register' ? styles.tabActive : ''}`}
            onClick={() => { setMode('register'); setError('') }}
          >注册</button>
        </div>

        {/* 登录表单 */}
        {mode === 'login' && (
          <form onSubmit={handleLogin} className={styles.form}>
            <div className={styles.field}>
              <label>账号</label>
              <input className="input" placeholder="输入用户名" value={username}
                onChange={e => setUsername(e.target.value)} required />
            </div>
            <div className={styles.field}>
              <label>密码</label>
              <input className="input" type="password" placeholder="输入密码" value={password}
                onChange={e => setPassword(e.target.value)} required />
            </div>
            {error && <div className={styles.error}>⚠️ {error}</div>}
            <button className="btn btn-primary btn-block btn-lg" type="submit" disabled={loading}>
              {loading ? '登录中…' : '🚀 开始冒险'}
            </button>
          </form>
        )}

        {/* 注册表单 */}
        {mode === 'register' && (
          <form onSubmit={handleRegister} className={styles.form}>
            <div className={styles.roleSelect}>
              <button type="button"
                className={`${styles.roleBtn} ${role === 'parent' ? styles.roleBtnActive : ''}`}
                onClick={() => setRole('parent')}>
                👨‍👩‍👦 我是家长
              </button>
            </div>
            <div className={styles.field}>
              <label>用户名</label>
              <input className="input" placeholder="设置用户名" value={username}
                onChange={e => setUsername(e.target.value)} required />
            </div>
            <div className={styles.field}>
              <label>昵称</label>
              <input className="input" placeholder="您的昵称" value={nickname}
                onChange={e => setNickname(e.target.value)} />
            </div>
            <div className={styles.field}>
              <label>密码</label>
              <input className="input" type="password" placeholder="设置密码（6位以上）" value={password}
                onChange={e => setPassword(e.target.value)} required />
            </div>
            {error && <div className={styles.error}>⚠️ {error}</div>}
            <button className="btn btn-teal btn-block btn-lg" type="submit" disabled={loading}>
              {loading ? '注册中…' : '✨ 创建账号'}
            </button>
          </form>
        )}

        <p className={styles.tip}>💡 演示体验：先注册家长账号，再创建孩子</p>
      </div>
    </div>
  )
}
