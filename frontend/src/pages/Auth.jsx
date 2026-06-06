import api from '../api'
import { useState } from 'react'

export default function Auth() {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [roleId, setRoleId] = useState(1) // 1 = courier, 2 = dispatcher
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (mode === 'register' && password !== confirmPassword) {
      setError('Пароли не совпадают')
      return
    }

    const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register'

    setLoading(true)
    try {
      const response = await api.post(endpoint, {
        email,
        password,
        ...(mode === 'register' && { role_id: roleId }),
      })

      if (mode === 'login') {
        const token = response.data.access_token

        // Достаём роль из JWT payload (средняя часть токена)
        const decoded = JSON.parse(atob(token.split('.')[1]))

        localStorage.setItem('token', token)
        localStorage.setItem('email', email)
        localStorage.setItem('role', decoded.role)

        // Редирект в зависимости от роли
        window.location.href = decoded.role === 2 ? '/dispatcher' : '/courier'
      } else {
        setMode('login')
        setError('')
        alert('Аккаунт создан! Теперь войдите.')
      }
    } catch (err) {
      if (err.response && err.response.data) {
        setError(err.response.data.detail || 'Ошибка сервера')
      } else {
        setError('Нет связи с сервером')
      }
    } finally {
      setLoading(false)
    }
  }

  const switchMode = (newMode) => {
    setMode(newMode)
    setError('')
    setEmail('')
    setPassword('')
    setConfirmPassword('')
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>
          {mode === 'login' ? 'Войти в аккаунт' : 'Регистрация'}
        </h2>

        <form onSubmit={handleSubmit} style={styles.form}>

          <div style={styles.inputGroup}>
            <label style={styles.label}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={styles.input}
              placeholder="example@mail.com"
            />
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={styles.input}
              placeholder="Введите пароль"
            />
          </div>

          {mode === 'register' && (
            <>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Повторите пароль</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  style={styles.input}
                  placeholder="Повторите пароль"
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Роль</label>
                <div style={styles.roleToggle}>
                  <button
                    type="button"
                    onClick={() => setRoleId(1)}
                    style={{ ...styles.roleBtn, ...(roleId === 1 ? styles.roleBtnActive : {}) }}
                  >
                    🚴 Курьер
                  </button>
                  <button
                    type="button"
                    onClick={() => setRoleId(2)}
                    style={{ ...styles.roleBtn, ...(roleId === 2 ? styles.roleBtnActive : {}) }}
                  >
                    🖥️ Диспетчер
                  </button>
                </div>
              </div>
            </>
          )}

          {error && <p style={styles.error}>{error}</p>}

          <button type="submit" style={{ ...styles.button, opacity: loading ? 0.6 : 1 }} disabled={loading}>
            {loading ? 'Загрузка...' : mode === 'login' ? 'Войти' : 'Создать аккаунт'}
          </button>
        </form>

        <div style={styles.footer}>
          {mode === 'login' ? (
            <p>Нет аккаунта?{' '}
              <span style={styles.link} onClick={() => switchMode('register')}>
                Зарегистрироваться
              </span>
            </p>
          ) : (
            <p>Уже есть аккаунт?{' '}
              <span style={styles.link} onClick={() => switchMode('login')}>
                Войти
              </span>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '80vh',
    fontFamily: 'Arial, sans-serif',
  },
  card: {
    background: '#1a1a1a',
    padding: '30px',
    borderRadius: '12px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
    width: '100%',
    maxWidth: '400px',
    textAlign: 'left',
    border: '1px solid #333',
  },
  title: {
    marginBottom: '20px',
    textAlign: 'center',
    color: '#fff',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
  },
  inputGroup: {
    marginBottom: '15px',
  },
  label: {
    display: 'block',
    marginBottom: '5px',
    color: '#aaa',
    fontSize: '14px',
  },
  input: {
    width: '100%',
    padding: '10px',
    borderRadius: '6px',
    border: '1px solid #444',
    background: '#242424',
    color: '#fff',
    boxSizing: 'border-box',
    fontSize: '14px',
  },
  roleToggle: {
    display: 'flex',
    gap: '10px',
  },
  roleBtn: {
    flex: 1,
    padding: '10px',
    borderRadius: '6px',
    border: '1px solid #444',
    background: '#242424',
    color: '#aaa',
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'all 0.2s',
  },
  roleBtnActive: {
    border: '1px solid #646cff',
    background: '#2a2a4a',
    color: '#fff',
    fontWeight: 'bold',
  },
  error: {
    color: '#ff4d4d',
    fontSize: '14px',
    marginBottom: '10px',
    textAlign: 'center',
  },
  button: {
    background: '#646cff',
    color: 'white',
    padding: '12px',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: 'bold',
    marginTop: '10px',
    transition: 'background 0.2s',
  },
  footer: {
    marginTop: '20px',
    textAlign: 'center',
    color: '#aaa',
    fontSize: '14px',
  },
  link: {
    color: '#646cff',
    cursor: 'pointer',
    textDecoration: 'underline',
  },
}