import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav style={styles.nav}>
      <Link to="/dispatcher" style={styles.link}>Диспетчер</Link>
      <Link to="/monitoring" style={styles.link}>Мониторинг</Link>
      <Link to="/courier" style={styles.link}>Курьер</Link>
    </nav>
  )
}

const styles = {
  nav: {
    display: 'flex',
    gap: '20px',
    padding: '15px',
    background: '#242424',
    borderBottom: '1px solid #444'
  },
  link: {
    color: '#646cff',
    textDecoration: 'none',
    fontWeight: 'bold'
  }
}