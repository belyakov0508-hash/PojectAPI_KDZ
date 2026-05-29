import { useState } from 'react'
import './App.css'

function App() {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (mode === 'login') {
      alert(`Вход с данными: ${email}`)
      // Здесь в будущем будет запрос к твоему database.py
    } else {
      if (password !== confirmPassword) {
        alert('Пароли не совпадают!')
        return
      }
      alert(`Регистрация пользователя: ${email}`)
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>
          {mode === 'login' ? 'Войти в аккаунт' : 'Регистрация'}
        </h2>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Email / Логин</label>
            <input
              type="email"
              placeholder="example@mail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={styles.input}
            />
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>Пароль</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={styles.input}
            />
          </div>

          {/* Если режим регистрации, показываем дополнительное поле */}
          {mode === 'register' && (
            <div style={styles.inputGroup}>
              <label style={styles.label}>Повторите пароль</label>
              <input
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                style={styles.input}
              />
            </div>
          )}

          <button type="submit" style={styles.button}>
            {mode === 'login' ? 'Войти' : 'Создать аккаунт'}
          </button>
        </form>

        <div style={styles.footer}>
          {mode === 'login' ? (
            <p>
              Нет аккаунта?{' '}
              <span style={styles.link} onClick={() => setMode('register')}>
                Зарегистрироваться
              </span>
            </p>
          ) : (
            <p>
              Уже есть аккаунт?{' '}
              <span style={styles.link} onClick={() => setMode('login')}>
                Войти
              </span>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

// Простые встроенные стили, чтобы форма выглядела аккуратно
const styles = {
  container: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '80vh',
    fontFamily: 'Arial, sans-serif'
  },
  card: {
    background: '#1a1a1a',
    padding: '30px',
    borderRadius: '12px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
    width: '100%',
    maxWidth: '400px',
    textAlign: 'left',
    border: '1px solid #333'
  },
  title: {
    marginBottom: '20px',
    textAlign: 'center',
    color: '#fff'
  },
  form: {
    display: 'flex',
    flexDirection: 'column'
  },
  inputGroup: {
    marginBottom: '15px'
  },
  label: {
    display: 'block',
    marginBottom: '5px',
    color: '#aaa',
    fontSize: '14px'
  },
  input: {
    width: '100%',
    padding: '10px',
    borderRadius: '6px',
    border: '1px solid #444',
    background: '#242424',
    color: '#fff',
    boxSizing: 'border-box'
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
    transition: 'background 0.2s'
  },
  footer: {
    marginTop: '20px',
    textAlign: 'center',
    color: '#aaa',
    fontSize: '14px'
  },
  link: {
    color: '#646cff',
    cursor: 'pointer',
    textDecoration: 'underline'
  }
}

export default App