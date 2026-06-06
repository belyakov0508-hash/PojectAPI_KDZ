import { Link } from 'react-router-dom'

export default function Navbar() {
  const role = parseInt(localStorage.getItem('role'))

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('email')
    window.location.href = '/login'
  }

  return (
    <nav style={styles.nav}>
      {role === 2 && (
        <>
          <Link to="/dispatcher" style={styles.link}>Загрузка данных</Link>
          <Link to="/monitoring" style={styles.link}>Мониторинг курьеров</Link>
        </>
      )}
      {role === 1 && (
        <Link to="/courier" style={styles.link}>Мои заказы</Link>
      )}
      <button onClick={handleLogout} style={styles.logout}>Выйти</button>
    </nav>
  )
}

const styles = {
  nav: {
    display: 'flex',
    gap: '20px',
    padding: '15px',
    background: '#242424',
    borderBottom: '1px solid #444',
    alignItems: 'center',
  },
  link: {
    color: '#646cff',
    textDecoration: 'none',
    fontWeight: 'bold',
  },
  logout: {
    marginLeft: 'auto',
    background: 'transparent',
    border: '1px solid #555',
    color: '#aaa',
    padding: '6px 12px',
    borderRadius: '5px',
    cursor: 'pointer',
    fontSize: '14px',
  },
}