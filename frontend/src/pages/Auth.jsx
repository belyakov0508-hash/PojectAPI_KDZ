import api from '../api' // Импорт нашего настроенного axios-клиента
import { useState } from 'react'

export default function Auth() {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const handleSubmit = async (e) => {
  e.preventDefault()

  // Допустим, бэкенд сделал такие эндпоинты в папке api/
  const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register'

  try {
    // Отправляем запрос на эндпоинт бэкенда
    const response = await api.post(endpoint, {
      email: email,       // Эти поля должны в точности совпадать
      password: password  // со схемой Pydantic (schemas/) на бэкенде!
    })

    alert(response.data.message)

    if (mode === 'login') {
      window.location.href = '/dispatcher' // уходим на роутинг страниц
    }
  } catch (error) {
    if (error.response && error.response.data) {
      // Выводим ошибку валидации Pydantic или HTTPException из FastAPI
      alert(error.response.data.detail || 'Ошибка эндпоинта')
    }
  }
}

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>{mode === 'login' ? 'Войти в аккаунт' : 'Регистрация'}</h2>
        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Email / Логин</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required style={styles.input} />
          </div>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Пароль</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required style={styles.input} />
          </div>
          {mode === 'register' && (
            <div style={styles.inputGroup}>
              <label style={styles.label}>Повторите пароль</label>
              <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required style={styles.input} />
            </div>
          )}
          <button type="submit" style={styles.button}>{mode === 'login' ? 'Войти' : 'Создать аккаунт'}</button>
        </form>
        <div style={styles.footer}>
          {mode === 'login' ? (
            <p>Нет аккаунта? <span style={styles.link} onClick={() => setMode('register')}>Зарегистрироваться</span></p>
          ) : (
            <p>Уже есть аккаунт? <span style={styles.link} onClick={() => setMode('login')}>Войти</span></p>
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